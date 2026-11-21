"""Data-pipeline validation: input checks that must pass before a PCF is published.

Each check returns PASS / WARN / FAIL with a detail message. FAIL blocks the
pipeline (non-zero exit in the CLI and CI).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .config import Study
from .uncertainty import PEDIGREE_INDICATORS

BOM_COLUMNS = {"component_id", "component_name", "material_class", "ef_basis", "mass_g", "qty", "process",
               "supplier_id", "origin_geography", "recycled_content_pct", "is_packaging", "excluded"}
EF_COLUMNS = {"ef_id", "name", "category", "material_class", "technology", "geography", "unit", "value_kgco2e",
              "reference_year", "reliability", "completeness", "technological"}


@dataclass
class Check:
    scope: str
    check: str
    status: str
    detail: str


def _ok(cond: bool, warn: bool = False) -> str:
    return "PASS" if cond else ("WARN" if warn else "FAIL")


def validate_ef_library(study: Study) -> list[Check]:
    ef = study.ef_library
    out = [Check("ef_library", "required columns", _ok(EF_COLUMNS <= set(ef.columns)),
                 f"missing: {sorted(EF_COLUMNS - set(ef.columns))}" if not EF_COLUMNS <= set(ef.columns) else "all present")]
    dup = ef["ef_id"][ef["ef_id"].duplicated()].tolist()
    out.append(Check("ef_library", "unique ef_id", _ok(not dup), f"duplicates: {dup}" if dup else f"{len(ef)} factors"))
    neg = ef.loc[ef["value_kgco2e"] <= 0, "ef_id"].tolist()
    out.append(Check("ef_library", "positive values", _ok(not neg), f"non-positive: {neg}" if neg else "ok"))
    bad_ped = ef.loc[~ef[["reliability", "completeness", "technological"]].isin([1, 2, 3, 4, 5]).all(axis=1), "ef_id"].tolist()
    out.append(Check("ef_library", "pedigree scores in 1-5", _ok(not bad_ped), f"invalid: {bad_ped}" if bad_ped else "ok"))
    future = ef.loc[ef["reference_year"] > study.reference_year, "ef_id"].tolist()
    out.append(Check("ef_library", "reference year <= study year", _ok(not future), f"future-dated: {future}" if future else "ok"))
    old = ef.loc[study.reference_year - ef["reference_year"] > 6, "ef_id"].tolist()
    out.append(Check("ef_library", "dataset age <= 6 years", _ok(not old, warn=True),
                     f"older datasets (temporal penalty applied): {old}" if old else "ok"))
    unknown_geo = sorted(set(ef["geography"]) - set(study.regions))
    out.append(Check("ef_library", "geographies in region hierarchy", _ok(not unknown_geo),
                     f"unknown: {unknown_geo}" if unknown_geo else "ok"))
    return out


def validate_product(study: Study, pid: str, total_kgco2e: float | None = None) -> list[Check]:
    bom, cfg, s = study.boms[pid], study.products[pid], study.settings
    ef = study.ef_library
    out: list[Check] = []
    add = lambda name, status, detail: out.append(Check(pid, name, status, detail))

    missing = BOM_COLUMNS - set(bom.columns)
    add("BOM required columns", _ok(not missing), f"missing: {sorted(missing)}" if missing else "all present")
    if missing:
        return out

    dup = bom["component_id"][bom["component_id"].duplicated()].tolist()
    add("unique component ids", _ok(not dup), f"duplicates: {dup}" if dup else "ok")
    bad = bom.loc[(bom["mass_g"] <= 0) | (bom["qty"] <= 0), "component_id"].tolist()
    add("positive mass and quantity", _ok(not bad), f"invalid: {bad}" if bad else "ok")
    bad = bom.loc[~bom["recycled_content_pct"].between(0, 100), "component_id"].tolist()
    add("recycled content 0-100%", _ok(not bad), f"invalid: {bad}" if bad else "ok")
    bad = bom.loc[~bom["ef_basis"].isin(["mass", "unit"]), "component_id"].tolist()
    add("ef_basis is mass|unit", _ok(not bad), f"invalid: {bad}" if bad else "ok")
    bad = bom.loc[~bom["process"].isin(study.process_energy.index), "component_id"].tolist()
    add("process in process-energy table", _ok(not bad), f"unknown process: {bad}" if bad else "ok")

    live = bom[~bom["excluded"]]
    unmapped = []
    for _, r in live.iterrows():
        unit = "kg" if r["ef_basis"] == "mass" else "unit"
        if ef[(ef["material_class"] == r["material_class"]) & (ef["unit"] == unit)].empty:
            unmapped.append(f"{r['component_id']}:{r['material_class']}/{unit}")
    add("every material mapped to an emission factor", _ok(not unmapped),
        f"unmapped: {unmapped}" if unmapped else f"{len(live)} lines mapped")
    no_group = sorted(set(live["material_class"]) - set(s["material_groups"]))
    add("every material has an end-of-life group", _ok(not no_group), f"missing: {no_group}" if no_group else "ok")
    no_rec = [r["component_id"] for _, r in live[live["recycled_content_pct"] > 0].iterrows()
              if ef[(ef["material_class"] == r["material_class"]) & (ef["technology"] == "recycled")].empty]
    add("recycled-content lines have a recycled dataset", _ok(not no_rec, warn=True),
        f"virgin factor used for: {no_rec}" if no_rec else "ok")

    tol = s["study"]["mass_tolerance_pct"]
    prod = bom[~bom["is_packaging"]]
    m = float((prod["mass_g"] * prod["qty"]).sum())
    dev = abs(m - cfg["declared_product_mass_g"]) / cfg["declared_product_mass_g"] * 100
    add("mass balance: product", _ok(dev <= tol), f"BOM {m:.1f} g vs declared {cfg['declared_product_mass_g']} g ({dev:.2f}%)")
    pk = bom[bom["is_packaging"]]
    m = float((pk["mass_g"] * pk["qty"]).sum())
    dev = abs(m - cfg["declared_packaging_mass_g"]) / cfg["declared_packaging_mass_g"] * 100
    add("mass balance: packaging", _ok(dev <= tol), f"BOM {m:.1f} g vs declared {cfg['declared_packaging_mass_g']} g ({dev:.2f}%)")

    cut = s["study"]["cutoff"]
    total_mass = float((bom["mass_g"] * bom["qty"]).sum())
    exc = bom[bom["excluded"]]
    exc_mass = float((exc["mass_g"] * exc["qty"]).sum())
    share = exc_mass / total_mass * 100
    add("cut-off: excluded mass share", _ok(share <= cut["mass_threshold_pct"]),
        f"{exc_mass:.1f} g excluded = {share:.2f}% (limit {cut['mass_threshold_pct']}%)")
    if total_kgco2e:
        est = exc_mass / 1000 * cut["proxy_ef_kgco2e_per_kg"]
        ishare = est / total_kgco2e * 100
        add("cut-off: estimated excluded impact", _ok(ishare <= cut["impact_threshold_pct"], warn=True),
            f"~{est:.4f} kg CO2e at proxy {cut['proxy_ef_kgco2e_per_kg']} kg/kg = {ishare:.2f}% of PCF")
    return out


def validate_settings(study: Study) -> list[Check]:
    out = []
    for region, r in study.settings["end_of_life"].items():
        sums = {f"collected.{g}": sum(v.values()) for g, v in r["collected"].items()}
        sums["uncollected"] = sum(r["uncollected"].values())
        sums.update({f"packaging.{g}": sum(v.values()) for g, v in r["packaging"].items()})
        bad = {k: round(v, 3) for k, v in sums.items() if abs(v - 1) > 1e-6}
        out.append(Check("settings", f"EoL fractions sum to 1 ({region})", _ok(not bad), f"bad: {bad}" if bad else "ok"))
        treat = {t for g in r["collected"].values() for t in g} | set(r["uncollected"])
        missing = [f"{g}:{t}" for g in study.settings["treatment_ef_map"]
                   for t in treat if t in ("incineration", "landfill") and t not in study.settings["treatment_ef_map"][g]]
        out.append(Check("settings", f"treatment factors defined ({region})", _ok(not missing),
                         f"missing: {missing}" if missing else "ok"))
    alloc = study.settings["study"]["allocation"]["factory_overhead_key"]
    out.append(Check("settings", "allocation key valid", _ok(alloc in ("mass", "units", "economic")), alloc))
    fa = set(study.factory_allocation["product_id"])
    missing = sorted(set(study.products) - fa)
    out.append(Check("settings", "all products in factory allocation table", _ok(not missing),
                     f"missing: {missing}" if missing else "ok"))
    return out


def validate_study(study: Study, totals: dict | None = None) -> pd.DataFrame:
    checks = validate_ef_library(study) + validate_settings(study)
    for pid in study.products:
        checks += validate_product(study, pid, (totals or {}).get(pid))
    return pd.DataFrame([asdict(c) for c in checks])


__all__ = ["validate_study", "validate_product", "validate_ef_library", "validate_settings", "PEDIGREE_INDICATORS"]
