"""ISO 14067-structured PCF study report (Markdown) and a PACT-style data-exchange JSON."""
from __future__ import annotations

import uuid
from datetime import date

import pandas as pd

from .calculator import STAGE_LABELS, STAGES, PCFResult
from .config import Study
from .uncertainty import dqr_label


def _table(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = [format(v, floatfmt) if isinstance(v, float) else str(v) for v in r]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def pcf_report(study: Study, res: PCFResult, mc: dict, tornado: pd.DataFrame, alloc: pd.DataFrame,
               scen: pd.DataFrame, checks: pd.DataFrame) -> str:
    st = study.settings["study"]
    m = res.meta
    stage = pd.DataFrame({"Stage": [STAGE_LABELS[s] for s in STAGES],
                          "kg CO2e": [res.by_stage[s] for s in STAGES],
                          "Share %": [res.by_stage[s] / res.total * 100 for s in STAGES]})
    hs = res.hotspots(8).rename(columns={"hotspot": "Hotspot", "kgco2e": "kg CO2e", "share_pct": "Share %"})
    sup = res.supplier_decisions[["component_id", "supplier_id", "pcf_kgco2e_per_unit", "reference_year",
                                  "verification", "decision", "reason"]] if not res.supplier_decisions.empty else pd.DataFrame()
    bio = res.biogenic
    bio_txt = ("No fibre-based materials." if bio.empty else
               f"Biogenic CO2 removal in fibre packaging: **{bio['removal_kgco2'].sum():.3f} kg CO2**; "
               f"released at end of life: {bio['eol_release_kgco2'].sum():.3f}; stored in landfill: "
               f"{bio['stored_in_landfill_kgco2'].sum():.3f}; transferred to recycling: "
               f"{bio['transferred_to_recycling_kgco2'].sum():.3f}. Reported separately and **not** included in the PCF total.")
    credits = res.credits["credit_kgco2e"].sum() if not res.credits.empty else 0.0
    torn = tornado[["parameter", "low_delta_pct", "high_delta_pct"]].rename(
        columns={"parameter": "Parameter (±20%)", "low_delta_pct": "−20% → Δ%", "high_delta_pct": "+20% → Δ%"})
    sc = scen[scen["product_id"] == res.product_id][["scenario", "total_kgco2e", "change_vs_baseline_pct"]]
    chk = checks[checks["scope"].isin([res.product_id, "ef_library", "settings"])]
    n_fail, n_warn = (chk["status"] == "FAIL").sum(), (chk["status"] == "WARN").sum()
    sel = res.selection_log[res.selection_log["component_id"] != ""][["component_id", "role", "selected_ef",
                                                                       "applicability_score", "n_candidates"]]

    return f"""# Product Carbon Footprint study — {m['name']}

*Generated {date.today().isoformat()} by `pcf-lca-engine`. Fictional product, illustrative emission factors.*

## 1. Result

| | |
|---|---|
| **PCF (cradle-to-grave, excl. biogenic)** | **{res.total:.2f} kg CO2e** per declared unit |
| 95% interval (Monte Carlo, {mc['n']:,} runs) | {mc['p2_5']:.2f} – {mc['p97_5']:.2f} kg CO2e (CV {mc['cv_pct']:.1f}%) |
| Primary data share (PACT definition) | {res.primary_data_share:.1f}% |
| Data quality rating (contribution-weighted) | {res.dqr:.2f} — {dqr_label(res.dqr)} |
| Recycling credits (reported separately) | {credits:.3f} kg CO2e |

## 2. Goal and scope

- **Declared unit:** {m['declared_unit']}
- **Intended application:** {st['intended_application']}
- **System boundary:** {st['system_boundary']}
- **GWP method:** {st['gwp_method']}
- **System model / end-of-life allocation:** {st['system_model']}
- **Reference year:** {st['reference_year']}
- **Excluded:** {"; ".join(st['excluded_processes'])}
- **Cut-off:** excluded mass ≤ {st['cutoff']['mass_threshold_pct']}% and estimated impact ≤ {st['cutoff']['impact_threshold_pct']}%
- **Allocation:** factory overhead allocated by **{m['allocation_key']}** ({m['overhead_kwh_per_unit']:.3f} kWh/unit); alternatives tested in §6
- **Use phase:** {m['lifetime_years']:g} years in {m['use_region']}, {m['kwh_per_year']:.3f} kWh/year
- **End of life:** {m['eol_region']} scenario, WEEE collection {m['weee_collection_rate']:.0%}

## 3. Results by life-cycle stage

{_table(stage)}

## 4. Hotspots

{_table(hs)}

## 5. Life cycle inventory and data sources

- Inventory lines: {len(res.inventory)} (see `inventory.csv`, each with activity amount, EF, pedigree scores and GSD²)
- Emission-factor selections with justification and competing candidates: `ef_selection_log.csv`

**Supplier-specific (primary) data**

{_table(sup) if not sup.empty else "None provided."}

**Material emission-factor selections**

{_table(sel)}

**Biogenic carbon (ISO 14067 requirement):** {bio_txt}

## 6. Interpretation (ISO 14044 §4.5)

**Sensitivity (one-at-a-time)**

{_table(torn, ".1f")}

**Allocation-key sensitivity**

{_table(alloc[["allocation_key", "overhead_kwh_per_unit", "total_kgco2e", "vs_mass_pct"]])}

**Eco-design scenarios**

{_table(sc.rename(columns={"total_kgco2e": "kg CO2e", "change_vs_baseline_pct": "Δ vs baseline %"}))}

## 7. Data quality and validation

{len(chk)} checks — {n_fail} FAIL, {n_warn} WARN.

{_table(chk[["check", "status", "detail"]])}

## 8. Limitations

- Emission factors are illustrative values in plausible ranges, not licensed ecoinvent / Sphera datasets.
- Monte Carlo covers emission-factor uncertainty only; activity-data uncertainty and correlations are not modelled.
- Distribution uses one representative Asia → Europe route for all markets.
- Replacement batteries' end-of-life is not modelled (below 1% of the total).
- Not third-party verified; not for comparative assertions disclosed to the public.

Warnings: {"; ".join(m['warnings']) if m['warnings'] else "none"}
"""


def pact_footprint(study: Study, res: PCFResult, mc: dict) -> dict:
    """PACT-inspired ProductFootprint record (simplified; not schema-validated)."""
    st = study.settings["study"]
    bio = res.biogenic
    bio_c = float(-bio["removal_kgco2"].sum() * 12 / 44) if not bio.empty else 0.0
    year = st["reference_year"]
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"pcf-lca-engine/{res.product_id}/{year}")),
        "specVersion": "PACT-style (simplified)",
        "companyName": "Fictional Peripherals Co.",
        "productIds": [f"urn:fictional:product:{res.product_id}"],
        "productDescription": res.meta["name"],
        "pcf": {
            "declaredUnit": "piece",
            "unitaryProductAmount": 1,
            "pCfExcludingBiogenic": round(res.total, 4),
            "fossilGhgEmissions": round(res.total, 4),
            "biogenicCarbonContent": round(bio_c, 4),
            "characterizationFactors": "AR6",
            "crossSectoralStandardsUsed": ["ISO Standard 14067", "GHG Protocol Product standard"],
            "boundaryProcessesDescription": st["system_boundary"],
            "referencePeriodStart": f"{year}-01-01T00:00:00Z",
            "referencePeriodEnd": f"{year}-12-31T23:59:59Z",
            "geographyRegionOrSubregion": "Europe",
            "primaryDataShare": round(res.primary_data_share, 1),
            "dqi": {"coveragePercent": 100.0, "dataQualityRating": round(res.dqr, 2)},
            "uncertaintyAssessmentDescription": (
                f"Monte Carlo ({mc['n']} runs), pedigree-derived lognormal: 95% interval "
                f"{mc['p2_5']:.3f}-{mc['p97_5']:.3f} kg CO2e"),
            "stageBreakdownKgCO2e": {s: round(v, 4) for s, v in res.by_stage.items()},
        },
    }
