"""End-to-end pipeline: validate -> calculate -> uncertainty -> sensitivity -> Scope 3 -> report."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import charts
from .calculator import calculate_pcf
from .config import Study, apply_scenario
from .report import pact_footprint, pcf_report
from .scope3 import scope3_inventory, scope3_rollup
from .sensitivity import allocation_sensitivity, scenario_comparison, tornado
from .uncertainty import monte_carlo, summarise_samples
from .validation import validate_study


class ValidationError(RuntimeError):
    pass


def run(study: Study, out_dir: Path, scenario: str = "baseline", mc_runs: int = 10_000, year: int = 2025,
        log=print) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if scenario != "baseline":
        study = apply_scenario(study, scenario)

    # 1. input validation (blocking)
    pre = validate_study(study)
    if (pre["status"] == "FAIL").any():
        pre.to_csv(out_dir / "validation_report.csv", index=False)
        raise ValidationError("Input validation failed:\n" + pre[pre["status"] == "FAIL"].to_string(index=False))
    log(f"✓ input validation: {len(pre)} checks, {(pre['status'] == 'WARN').sum()} warnings")

    # 2. product footprints
    results = {pid: calculate_pcf(study, pid) for pid in study.products}
    checks = validate_study(study, {p: r.total for p, r in results.items()})
    checks.to_csv(out_dir / "validation_report.csv", index=False)
    scen = scenario_comparison(study) if scenario == "baseline" else pd.DataFrame(
        columns=["scenario", "product_id", "total_kgco2e", "change_vs_baseline_pct"])

    summary = []
    for pid, res in results.items():
        pdir = out_dir / pid
        pdir.mkdir(exist_ok=True)
        samples = monte_carlo(res.inventory, n=mc_runs)
        mc = {**summarise_samples(samples, res.total), "n": mc_runs}
        torn = tornado(study, pid)
        alloc = allocation_sensitivity(study, pid)

        res.inventory.to_csv(pdir / "inventory.csv", index=False)
        res.selection_log.to_csv(pdir / "ef_selection_log.csv", index=False)
        res.supplier_decisions.to_csv(pdir / "supplier_data_decisions.csv", index=False)
        res.biogenic.to_csv(pdir / "biogenic_carbon.csv", index=False)
        res.credits.to_csv(pdir / "recycling_credits_reported_separately.csv", index=False)
        stages = res.by_stage.rename("kgco2e").to_frame()
        stages["share_pct"] = stages["kgco2e"] / res.total * 100
        stages.to_csv(pdir / "stage_summary.csv", index_label="stage")
        torn.to_csv(pdir / "sensitivity_tornado.csv", index=False)
        alloc.to_csv(pdir / "allocation_sensitivity.csv", index=False)
        (pdir / "monte_carlo_summary.json").write_text(json.dumps(mc, indent=2))
        (pdir / "pact_footprint.json").write_text(json.dumps(pact_footprint(study, res, mc), indent=2))
        (pdir / "PCF_report.md").write_text(pcf_report(study, res, mc, torn, alloc, scen, checks))

        charts.hotspots(res, pdir / "hotspots.png")
        charts.tornado(torn, pdir / "tornado.png")
        charts.monte_carlo(samples, mc, pid, pdir / "monte_carlo.png")

        summary.append({"product_id": pid, "total_kgco2e": round(res.total, 3), "p2_5": round(mc["p2_5"], 3),
                        "p97_5": round(mc["p97_5"], 3), "primary_data_share_pct": round(res.primary_data_share, 1),
                        "dqr": round(res.dqr, 2), "top_hotspot": res.hotspots(1)["hotspot"].iloc[0]})
        log(f"✓ {pid}: {res.total:.2f} kg CO2e (95% {mc['p2_5']:.2f}–{mc['p97_5']:.2f}), "
            f"PDS {res.primary_data_share:.0f}%, DQR {res.dqr:.2f}")

    pd.DataFrame(summary).to_csv(out_dir / "pcf_summary.csv", index=False)
    charts.stage_contribution(results, out_dir / "stage_contribution.png")

    # 3. portfolio outputs (baseline only)
    if scenario == "baseline":
        scen.to_csv(out_dir / "scenario_comparison.csv", index=False)
        charts.scenarios(scen, out_dir / "scenarios.png")
        s3 = scope3_rollup(study, year)
        for k, df in s3.items():
            df.to_csv(out_dir / f"scope3_{k}.csv", index=False)
        charts.scope3_categories(s3["by_category"], out_dir / "scope3_by_category.png")
        log(f"✓ Scope 3 FY{year}: {s3['by_category']['tco2e'].sum():,.0f} t CO2e across "
            f"{len(s3['by_category'])} categories")

        # 4. warehouse extracts for the SQL layer
        wh = out_dir / "warehouse"
        wh.mkdir(exist_ok=True)
        pd.concat([r.inventory for r in results.values()]).to_csv(wh / "fact_pcf_inventory.csv", index=False)
        scope3_inventory(study, year).to_csv(wh / "fact_unit_inventory_by_region.csv", index=False)
        study.units_sold.to_csv(wh / "fact_units_sold.csv", index=False)
        study.ef_library.to_csv(wh / "dim_emission_factor.csv", index=False)
        pd.DataFrame([{"product_id": p, "product_name": c["name"], "declared_unit": c["declared_unit"]}
                      for p, c in study.products.items()]).to_csv(wh / "dim_product.csv", index=False)

    return {"results": results, "checks": checks, "scenarios": scen}
