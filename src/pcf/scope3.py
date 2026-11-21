"""Roll product carbon footprints up to the brand owner's Scope 3 inventory.

Each product is recalculated for the market region it was sold in (use-phase grid
and end-of-life scenario differ by region), every inventory line is mapped to a
GHG Protocol Scope 3 category, and per-unit values are multiplied by units sold.
A spend-based (EEIO) estimate of Category 1 is produced alongside for comparison.
"""
from __future__ import annotations

import pandas as pd

from .calculator import calculate_pcf
from .config import Study
from .ef_library import EFLibrary

CATEGORY_NAMES = {
    1: "Cat 1 Purchased goods & services",
    4: "Cat 4 Upstream transportation & distribution",
    9: "Cat 9 Downstream transportation & distribution",
    11: "Cat 11 Use of sold products",
    12: "Cat 12 End-of-life treatment of sold products",
}


def map_category(stage: str, sub_stage: str, mapping: dict) -> int:
    key = f"{stage}:{sub_stage}"
    if key in mapping:
        return int(mapping[key])
    if stage in mapping:
        return int(mapping[stage])
    raise KeyError(f"No Scope 3 mapping for {key}")


def scope3_inventory(study: Study, year: int) -> pd.DataFrame:
    """Per-unit inventory for each (product, region) sold, with Scope 3 category."""
    mapping = study.settings["scope3"]["mapping"]
    sold = study.units_sold[study.units_sold["year"] == year]
    frames = []
    for _, s in sold.iterrows():
        res = calculate_pcf(study, s["product_id"], {"use_region": s["region"], "eol_region": s["region"]})
        inv = res.inventory[["product_id", "stage", "sub_stage", "item", "kgco2e", "data_type"]].copy()
        inv["region"] = s["region"]
        inv["scope3_category"] = [map_category(a, b, mapping) for a, b in zip(inv["stage"], inv["sub_stage"])]
        frames.append(inv)
    return pd.concat(frames, ignore_index=True)


def scope3_rollup(study: Study, year: int) -> dict[str, pd.DataFrame]:
    inv = scope3_inventory(study, year)
    sold = study.units_sold[study.units_sold["year"] == year]
    detail = inv.merge(sold[["product_id", "region", "units"]], on=["product_id", "region"])
    detail["tco2e"] = detail["kgco2e"] * detail["units"] / 1000.0

    by_cat = detail.groupby("scope3_category")["tco2e"].sum().reset_index()
    by_cat["category_name"] = by_cat["scope3_category"].map(CATEGORY_NAMES)
    by_cat["share_pct"] = by_cat["tco2e"] / by_cat["tco2e"].sum() * 100

    by_prod = detail.pivot_table(index=["product_id", "region"], columns="scope3_category", values="tco2e",
                                 aggfunc="sum", fill_value=0.0)
    by_prod.columns = [f"cat_{c}" for c in by_prod.columns]
    by_prod["total_tco2e"] = by_prod.sum(axis=1)
    by_prod = by_prod.reset_index()

    # spend-based comparison for Category 1
    cfg = study.settings["scope3"]["spend_based"]
    lib = EFLibrary(study.ef_library, study.regions, study.reference_year)
    eeio = float(lib.get(cfg["ef_id"])["value_kgco2e"])
    cat1 = detail[detail["scope3_category"] == 1].groupby("product_id")["tco2e"].sum()
    spend = sold.groupby("product_id")["revenue_eur"].sum() * cfg["cogs_ratio"]
    comp = pd.DataFrame({
        "product_based_cat1_tco2e": cat1,
        "purchased_cogs_eur": spend,
        "spend_based_cat1_tco2e": spend * eeio / 1000.0,
    })
    comp["difference_pct"] = (comp["spend_based_cat1_tco2e"] / comp["product_based_cat1_tco2e"] - 1) * 100
    return {"detail": detail, "by_category": by_cat, "by_product": by_prod,
            "spend_comparison": comp.reset_index().rename(columns={"index": "product_id"})}
