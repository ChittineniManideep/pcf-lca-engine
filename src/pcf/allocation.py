"""Allocation of shared factory overhead energy to products (ISO 14044 §4.3.4)."""
from __future__ import annotations

import pandas as pd

KEYS = ("mass", "units", "economic")


def allocation_shares(factory: pd.DataFrame, key: str) -> pd.Series:
    """Share of site overhead attributed to each product line (sums to 1)."""
    if key == "mass":
        basis = factory["annual_units"] * factory["unit_mass_g"]
    elif key == "units":
        basis = factory["annual_units"].astype(float)
    elif key == "economic":
        basis = factory["annual_units"] * factory["unit_revenue_eur"]
    else:
        raise ValueError(f"Allocation key must be one of {KEYS}")
    return pd.Series((basis / basis.sum()).values, index=factory["product_id"])


def overhead_kwh_per_unit(factory: pd.DataFrame, annual_kwh: float, key: str) -> pd.Series:
    shares = allocation_shares(factory, key)
    units = factory.set_index("product_id")["annual_units"]
    return shares * annual_kwh / units


def compare_keys(factory: pd.DataFrame, annual_kwh: float) -> pd.DataFrame:
    """kWh per unit under each allocation key — used for the allocation sensitivity check."""
    return pd.DataFrame({k: overhead_kwh_per_unit(factory, annual_kwh, k) for k in KEYS})
