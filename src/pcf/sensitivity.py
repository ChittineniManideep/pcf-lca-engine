"""Sensitivity analysis (ISO 14044 §4.5.3.3): one-at-a-time ±20% tornado,
allocation-key comparison, and eco-design scenario comparison."""
from __future__ import annotations

import pandas as pd

from .calculator import calculate_pcf
from .config import Study, apply_scenario

PARAMETERS = {
    "Production grid intensity": lambda f: {"grid_multiplier_production": f},
    "PCBA emission factor": lambda f: {"ef_multipliers": {"PCBA": f}},
    "Aluminium emission factor": lambda f: {"ef_multipliers": {"aluminium": f}},
    "Product lifetime": lambda f: {"lifetime_multiplier": f},
    "Use-phase power draw": lambda f: {"use_power_multiplier": f},
    "Ocean freight distance": lambda f: {"sea_km_multiplier": f},
    "WEEE collection rate": lambda f: {"collection_rate_multiplier": f},
}


def tornado(study: Study, pid: str, delta: float = 0.20) -> pd.DataFrame:
    base = calculate_pcf(study, pid).total
    rows = []
    for name, fn in PARAMETERS.items():
        lo = calculate_pcf(study, pid, fn(1 - delta)).total
        hi = calculate_pcf(study, pid, fn(1 + delta)).total
        rows.append({"parameter": name, "low_kgco2e": lo, "high_kgco2e": hi,
                     "low_delta_pct": (lo / base - 1) * 100, "high_delta_pct": (hi / base - 1) * 100,
                     "swing_kgco2e": abs(hi - lo)})
    df = pd.DataFrame(rows)
    df = df[df["swing_kgco2e"] > 1e-9].sort_values("swing_kgco2e", ascending=False)  # drop parameters not in this product
    df.insert(0, "product_id", pid)
    df["baseline_kgco2e"] = base
    return df.reset_index(drop=True)


def allocation_sensitivity(study: Study, pid: str) -> pd.DataFrame:
    rows = []
    for key in ("mass", "units", "economic"):
        r = calculate_pcf(study, pid, {"allocation_key": key})
        rows.append({"product_id": pid, "allocation_key": key, "overhead_kwh_per_unit": r.meta["overhead_kwh_per_unit"],
                     "total_kgco2e": r.total})
    df = pd.DataFrame(rows)
    df["vs_mass_pct"] = (df["total_kgco2e"] / df.loc[df["allocation_key"] == "mass", "total_kgco2e"].iloc[0] - 1) * 100
    return df


def scenario_comparison(study: Study) -> pd.DataFrame:
    rows = []
    for name, sc in study.scenarios.items():
        s = apply_scenario(study, name)
        for pid in s.products:
            r = calculate_pcf(s, pid)
            rows.append({"scenario": name, "description": sc["description"], "product_id": pid, "total_kgco2e": r.total,
                         **{f"{k}_kgco2e": v for k, v in r.by_stage.items()}})
    df = pd.DataFrame(rows)
    base = df[df["scenario"] == "baseline"].set_index("product_id")["total_kgco2e"]
    df["change_vs_baseline_pct"] = df.apply(lambda x: (x["total_kgco2e"] / base[x["product_id"]] - 1) * 100, axis=1)
    return df
