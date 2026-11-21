"""Cradle-to-grave product carbon footprint calculation (ISO 14067).

Builds a line-level life cycle inventory: every line is
    activity amount x emission factor = kg CO2e
with its data source, data type (primary / secondary) and pedigree scores, so the
result is fully traceable from BOM line to total.

Life-cycle stages
    raw_material_acquisition  materials and purchased components (cradle-to-gate)
    packaging                 retail packaging materials
    production                component processing, final assembly, allocated overhead
    distribution              inbound and outbound logistics
    use                       electricity and consumables over the product lifetime
    end_of_life               collection, recycling, incineration, landfill
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import pandas as pd

from .allocation import overhead_kwh_per_unit
from .config import Study
from .ef_library import EFLibrary, Selection
from .uncertainty import PEDIGREE_INDICATORS, dqr, gsd95, weighted_dqr
from .units import CO2_PER_C, g_to_kg, gross_input, tonne_km

STAGES = ["raw_material_acquisition", "packaging", "production", "distribution", "use", "end_of_life"]
STAGE_LABELS = {
    "raw_material_acquisition": "Raw materials",
    "packaging": "Packaging",
    "production": "Production",
    "distribution": "Distribution",
    "use": "Use",
    "end_of_life": "End of life",
}


@dataclass
class PCFResult:
    product_id: str
    inventory: pd.DataFrame
    selection_log: pd.DataFrame
    supplier_decisions: pd.DataFrame
    biogenic: pd.DataFrame
    credits: pd.DataFrame
    meta: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return float(self.inventory["kgco2e"].sum())

    @property
    def by_stage(self) -> pd.Series:
        return self.inventory.groupby("stage")["kgco2e"].sum().reindex(STAGES, fill_value=0.0)

    @property
    def primary_data_share(self) -> float:
        prim = self.inventory["data_type"].isin(["primary", "primary_activity"])
        return float(self.inventory.loc[prim, "kgco2e"].sum() / self.total * 100)

    @property
    def dqr(self) -> float:
        return weighted_dqr(self.inventory)

    def hotspots(self, n: int = 10) -> pd.DataFrame:
        inv = self.inventory.copy()
        names = (inv[inv["sub_stage"].isin(["materials", "supplier_pcf"])]
                 .drop_duplicates("component_id").set_index("component_id")["item"])
        comp = inv["component_id"].map(lambda c: f"{c} {names.get(c, '')}".strip())
        inv["hotspot"] = inv["item"].where(inv["component_id"] == "", comp)
        out = inv.groupby("hotspot")["kgco2e"].sum().sort_values(ascending=False).head(n).reset_index()
        out["share_pct"] = out["kgco2e"] / self.total * 100
        return out


def _blend_pedigree(a: dict, b: dict, share_b: float) -> dict:
    return {k: int(round((1 - share_b) * a[k] + share_b * b[k])) for k in PEDIGREE_INDICATORS}


class _Builder:
    def __init__(self, study: Study, product_id: str, overrides: dict | None):
        self.study = study
        self.pid = product_id
        self.cfg = study.products[product_id]
        self.bom = study.boms[product_id]
        self.ov = overrides or {}
        self.lib = EFLibrary(study.ef_library, study.regions, study.reference_year)
        self.lines: list[dict] = []
        self.log: list[dict] = []
        self.supplier: list[dict] = []
        self.biogenic: list[dict] = []
        self.credits: list[dict] = []
        self.warnings: list[str] = []

    # ------------------------------------------------------------- helpers
    def add(self, stage, sub_stage, item, amount, unit, ef_id, ef_value, ef_unit, category, pedigree,
            data_type="secondary", component_id="", note="", multiplier=1.0):
        self.lines.append({
            "product_id": self.pid, "stage": stage, "sub_stage": sub_stage, "component_id": component_id,
            "item": item, "activity_amount": amount, "activity_unit": unit, "ef_id": ef_id,
            "ef_value": ef_value * multiplier, "ef_unit": ef_unit, "kgco2e": amount * ef_value * multiplier,
            "data_type": data_type, "category": category, **pedigree, "note": note,
        })

    def log_selection(self, sel: Selection, role: str, component_id="", component_name="", origin=""):
        self.log.append({
            "product_id": self.pid, "component_id": component_id, "component_name": component_name,
            "role": role, "origin": origin, "selected_ef": sel.ef_id, "ef_value": sel.value, "unit": sel.unit,
            "applicability_score": sel.score, "n_candidates": len(sel.candidates), "justification": sel.reason,
            "candidates": "; ".join(f"{c['ef_id']}={c['score']}" for c in sel.candidates),
        })

    def grid(self, region: str, role: str, override: str | None = None) -> tuple[str, float, str, dict]:
        if override:
            row = self.lib.get(override)
            return override, float(row["value_kgco2e"]), row["unit"], self.lib.pedigree_for(override, region)
        sel = self.lib.select("electricity", region, ("grid_mix",), "kWh")
        self.log_selection(sel, role, origin=region)
        return sel.ef_id, sel.value, sel.unit, sel.pedigree

    def transport_ef(self, mode: str, region: str) -> Selection:
        sel = self.lib.select(mode, region, ("freight",), "tkm")
        self.log_selection(sel, f"transport:{mode}", origin=region)
        return sel

    # ------------------------------------------------------ supplier data
    def supplier_decision(self, row: pd.Series):
        sp = self.study.supplier_pcf
        match = sp[(sp["product_id"] == self.pid) & (sp["component_id"] == row["component_id"])]
        if match.empty:
            return None
        s = match.iloc[0]
        rules = self.study.settings["supplier_data_rules"]
        age = self.study.reference_year - int(s["reference_year"])
        reasons = []
        if s["boundary"] not in rules["accepted_boundaries"]:
            reasons.append(f"boundary '{s['boundary']}' not cradle-to-gate")
        if age > rules["max_age_years"]:
            reasons.append(f"reference year {int(s['reference_year'])} older than {rules['max_age_years']} years")
        if s["verification"] not in rules["reliability_by_verification"]:
            reasons.append(f"verification '{s['verification']}' not accepted")
        accepted = not reasons
        self.supplier.append({
            "product_id": self.pid, "component_id": row["component_id"], "supplier_id": s["supplier_id"],
            "pcf_kgco2e_per_unit": s["pcf_kgco2e_per_unit"], "boundary": s["boundary"],
            "reference_year": int(s["reference_year"]), "verification": s["verification"],
            "decision": "accepted" if accepted else "rejected",
            "reason": "meets boundary, age and verification rules" if accepted else "; ".join(reasons),
        })
        return s if accepted else None

    # -------------------------------------------------------- stages
    def materials_and_processing(self):
        proc = self.study.process_energy
        ef_mult = self.ov.get("ef_multipliers", {})
        grid_mult = self.ov.get("grid_multiplier_production", 1.0)

        for _, r in self.bom[~self.bom["excluded"]].iterrows():
            stage = "packaging" if r["is_packaging"] else "raw_material_acquisition"
            cid, cname, mclass, origin = r["component_id"], r["component_name"], r["material_class"], r["origin_geography"]

            sup = self.supplier_decision(r)
            if sup is not None:
                rel = self.study.settings["supplier_data_rules"]["reliability_by_verification"][sup["verification"]]
                ped = {"reliability": rel,
                       "completeness": 2 if sup["supplier_primary_data_share_pct"] >= 50 else 3,
                       "temporal": self.lib.temporal_score(sup["reference_year"]),
                       "geographical": 1, "technological": 1}
                self.add(stage, "supplier_pcf", cname, float(r["qty"]), "unit",
                         f"SUPPLIER:{sup['supplier_id']}", float(sup["pcf_kgco2e_per_unit"]), "unit",
                         "primary", ped, data_type="primary", component_id=cid,
                         note=f"Supplier cradle-to-gate PCF ({sup['method']}, {sup['verification']})",
                         multiplier=ef_mult.get(mclass, 1.0))
                continue

            if r["ef_basis"] == "unit":
                sel = self.lib.select(mclass, origin, None, "unit")
                self.log_selection(sel, "component", cid, cname, origin)
                self.add(stage, "materials", cname, float(r["qty"]), "unit", sel.ef_id, sel.value, sel.unit,
                         sel.category, sel.pedigree, component_id=cid, multiplier=ef_mult.get(mclass, 1.0))
                continue

            process = r["process"] if r["process"] in proc.index else "none"
            scrap = float(proc.loc[process, "scrap_rate"])
            net_kg = g_to_kg(float(r["mass_g"]) * float(r["qty"]))
            gross_kg = gross_input(net_kg, scrap)
            rc = float(r["recycled_content_pct"]) / 100.0

            virgin = self.lib.select(mclass, origin, ("virgin", "generic"), "kg")
            self.log_selection(virgin, "material:virgin" if rc else "material", cid, cname, origin)
            ef_id, value, ped, note = virgin.ef_id, virgin.value, virgin.pedigree, ""
            if rc > 0:
                try:
                    rec = self.lib.select(mclass, origin, ("recycled",), "kg")
                    self.log_selection(rec, "material:recycled", cid, cname, origin)
                    value = (1 - rc) * virgin.value + rc * rec.value
                    ef_id = f"{virgin.ef_id}|{rec.ef_id}@{int(rc * 100)}%"
                    ped = _blend_pedigree(virgin.pedigree, rec.pedigree, rc)
                    note = f"{int(rc * 100)}% recycled content blended"
                except LookupError:
                    self.warnings.append(f"{cid}: no recycled dataset for {mclass}; virgin factor applied (conservative)")
            if scrap:
                note = (note + "; " if note else "") + f"gross input incl. {scrap:.0%} process scrap"
            self.add(stage, "materials", cname, gross_kg, "kg", ef_id, value, "kg", virgin.category, ped,
                     component_id=cid, note=note, multiplier=ef_mult.get(mclass, 1.0))

            kwh = gross_kg * float(proc.loc[process, "kwh_per_kg"])
            if kwh > 0:
                g_id, g_val, g_unit, g_ped = self.grid(origin, "electricity:component_processing")
                g_ped = {**g_ped, "technological": max(g_ped["technological"], 3)}
                self.add("production", "component_processing", f"{cname} — {process}", kwh, "kWh", g_id, g_val,
                         g_unit, "energy", g_ped, component_id=cid, note="generic process energy intensity",
                         multiplier=grid_mult)

    def assembly_and_overhead(self):
        m = self.cfg["manufacturing"]
        site = m["assembly_site"]
        override = m.get("grid_ef_override")
        grid_mult = self.ov.get("grid_multiplier_production", 1.0)
        g_id, g_val, g_unit, g_ped = self.grid(site, "electricity:assembly", override)
        self.add("production", "final_assembly", "Final assembly & test (metered)", m["assembly_energy_kwh_per_unit"],
                 "kWh", g_id, g_val, g_unit, "energy", g_ped, data_type="primary_activity", multiplier=grid_mult)

        key = self.ov.get("allocation_key", self.study.settings["study"]["allocation"]["factory_overhead_key"])
        fac = self.study.settings["factory"]
        per_unit = overhead_kwh_per_unit(self.study.factory_allocation, fac["annual_overhead_kwh"], key)
        kwh = float(per_unit[self.pid])
        self.add("production", "factory_overhead", f"Factory overhead ({key} allocation)", kwh, "kWh", g_id, g_val,
                 g_unit, "energy", {**g_ped, "completeness": max(g_ped["completeness"], 2)},
                 data_type="primary_activity", note=f"site-metered overhead allocated by {key}", multiplier=grid_mult)
        self.meta_alloc = {"allocation_key": key, "overhead_kwh_per_unit": kwh}

    def distribution(self):
        d = self.cfg["distribution"]
        live = self.bom[~self.bom["excluded"]]
        mass_kg = lambda df: g_to_kg(float((df["mass_g"] * df["qty"]).sum()))
        product_kg, packaging_kg = mass_kg(live[~live["is_packaging"]]), mass_kg(live[live["is_packaging"]])
        self.masses = {"product_kg": product_kg, "packaging_kg": packaging_kg}

        for leg in d["inbound"]:
            sel = self.transport_ef(leg["mode"], leg["region"])
            tkm = tonne_km(product_kg + packaging_kg, leg["distance_km"])
            self.add("distribution", leg["leg"], f"Supplier → assembly ({leg['mode']})", tkm, "tkm", sel.ef_id,
                     sel.value, sel.unit, "transport", sel.pedigree)

        ship_kg = (product_kg + packaging_kg) * d.get("logistics_overhead_factor", 1.0)
        air = float(d.get("air_freight_share", 0.0))
        for leg in d["outbound"]:
            km = leg["distance_km"]
            if leg["mode"] == "sea":
                km *= self.ov.get("sea_km_multiplier", 1.0)
                sea = self.transport_ef("sea", leg["region"])
                self.add("distribution", leg["leg"], "Ocean freight", tonne_km(ship_kg, km) * (1 - air), "tkm",
                         sea.ef_id, sea.value, sea.unit, "transport", sea.pedigree, note=f"{1 - air:.0%} of units")
                if air > 0:
                    a = self.transport_ef("air", "GLO")
                    self.add("distribution", leg["leg"], "Air freight (expedited)",
                             tonne_km(ship_kg, d["air_distance_km"]) * air, "tkm", a.ef_id, a.value, a.unit,
                             "transport", a.pedigree, note=f"{air:.0%} of units")
            else:
                sel = self.transport_ef(leg["mode"], leg["region"])
                self.add("distribution", leg["leg"], f"{leg['leg'].replace('_', ' ')} ({leg['mode']})",
                         tonne_km(ship_kg, km), "tkm", sel.ef_id, sel.value, sel.unit, "transport", sel.pedigree)

    def use(self):
        u = self.cfg["use"]
        region = self.ov.get("use_region", u["region"])
        life = u["lifetime_years"] * self.ov.get("lifetime_multiplier", 1.0)
        pm = self.ov.get("use_power_multiplier", 1.0)
        kwh_year = (u["battery_wh_per_charge"] * u["charges_per_year"] / max(u["charger_efficiency"], 1e-9)
                    + u["receiver_power_w"] * u["active_hours_per_year"]) / 1000.0 * pm
        g_id, g_val, g_unit, g_ped = self.grid(region, "electricity:use")
        self.add("use", "electricity", f"Charging + receiver power, {life:g} years ({region})", kwh_year * life,
                 "kWh", g_id, g_val, g_unit, "energy", g_ped, note=f"{kwh_year:.3f} kWh/year")
        for c in u.get("consumables", []):
            sets = max(life / c["replacement_interval_years"] - c.get("initial_sets_in_bom", 0), 0)
            cells = sets * c["cells_per_set"]
            sel = self.lib.select(c["material_class"], region, None, "unit")
            self.log_selection(sel, "consumable", origin=region)
            self.add("use", "consumables", f"Replacement {c['material_class'].replace('_', ' ')} cells", cells,
                     "unit", sel.ef_id, sel.value, sel.unit, sel.category, sel.pedigree,
                     note="indirect use-phase emissions")
        self.meta_use = {"use_region": region, "lifetime_years": life, "kwh_per_year": kwh_year}

    def end_of_life(self):
        s = self.study.settings
        region = self.ov.get("eol_region", self.cfg["end_of_life"]["region"])
        rates = s["end_of_life"][region]
        coll = min(rates["weee_collection_rate"] * self.ov.get("collection_rate_multiplier", 1.0), 1.0)
        groups, tmap, bio = s["material_groups"], s["treatment_ef_map"], s["biogenic"]
        agg = defaultdict(float)

        for _, r in self.bom[~self.bom["excluded"]].iterrows():
            group = groups.get(r["material_class"])
            if group is None:
                self.warnings.append(f"{r['component_id']}: material class {r['material_class']} has no EoL group")
                continue
            kg = g_to_kg(float(r["mass_g"]) * float(r["qty"]))
            if r["is_packaging"]:
                fates = rates["packaging"][group]
            else:
                fates = defaultdict(float)
                for t, f in rates["collected"][group].items():
                    fates[t] += coll * f
                for t, f in rates["uncollected"].items():
                    fates[t] += (1 - coll) * f
            for t, f in fates.items():
                agg[(group, t, bool(r["is_packaging"]))] += kg * f

            # avoided-burden potential, reported separately (not in total)
            rec_frac = fates.get("recycling", 0.0)
            if rec_frac > 0:
                try:
                    v = self.lib.select(r["material_class"], "GLO", ("virgin",), "kg")
                    rc = self.lib.select(r["material_class"], "GLO", ("recycled",), "kg")
                    self.credits.append({"product_id": self.pid, "component_id": r["component_id"],
                                         "material_class": r["material_class"], "recycled_kg": kg * rec_frac,
                                         "credit_kgco2e": -kg * rec_frac * (v.value - rc.value)})
                except LookupError:
                    pass

            # biogenic carbon in fibre packaging
            cf = bio["carbon_fraction"].get(r["material_class"])
            if cf:
                co2 = kg * cf * CO2_PER_C
                released = co2 * (fates.get("incineration", 0) + fates.get("landfill", 0) * bio["landfill_release_fraction"])
                stored = co2 * fates.get("landfill", 0) * (1 - bio["landfill_release_fraction"])
                transferred = co2 * fates.get("recycling", 0)
                self.biogenic.append({"product_id": self.pid, "component_id": r["component_id"],
                                      "material_class": r["material_class"], "removal_kgco2": -co2,
                                      "eol_release_kgco2": released, "stored_in_landfill_kgco2": stored,
                                      "transferred_to_recycling_kgco2": transferred})

        for (group, treatment, pkg), kg in sorted(agg.items()):
            ef_id = tmap[group][treatment]
            row = self.lib.get(ef_id)
            ped = self.lib.pedigree_for(ef_id, region)
            self.add("end_of_life", treatment, f"{group} {'packaging' if pkg else 'product'} — {treatment}", kg, "kg",
                     ef_id, float(row["value_kgco2e"]), row["unit"], "eol", ped,
                     note=f"{region}, WEEE collection {coll:.0%}" if not pkg else f"{region} packaging scenario")
        self.meta_eol = {"eol_region": region, "weee_collection_rate": coll}

    # ---------------------------------------------------------------- run
    def run(self) -> PCFResult:
        self.materials_and_processing()
        self.assembly_and_overhead()
        self.distribution()
        self.use()
        self.end_of_life()

        inv = pd.DataFrame(self.lines)
        inv["dqr"] = inv.apply(lambda x: dqr({k: x[k] for k in PEDIGREE_INDICATORS}), axis=1)
        inv["gsd95"] = inv.apply(lambda x: gsd95({k: x[k] for k in PEDIGREE_INDICATORS}, x["category"]), axis=1)
        log = pd.DataFrame(self.log).drop_duplicates(subset=["component_id", "role", "origin", "selected_ef"])
        meta = {"product_id": self.pid, "name": self.cfg["name"], "declared_unit": self.cfg["declared_unit"],
                **self.masses, **self.meta_alloc, **self.meta_use, **self.meta_eol, "warnings": self.warnings}
        return PCFResult(self.pid, inv, log.reset_index(drop=True), pd.DataFrame(self.supplier),
                         pd.DataFrame(self.biogenic), pd.DataFrame(self.credits), meta)


def calculate_pcf(study: Study, product_id: str, overrides: dict | None = None) -> PCFResult:
    """Calculate the cradle-to-grave PCF of one declared unit of a product."""
    if product_id not in study.products:
        raise KeyError(f"Unknown product {product_id}. Available: {sorted(study.products)}")
    return _Builder(study, product_id, overrides).run()
