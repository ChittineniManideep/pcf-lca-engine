import numpy as np
import pytest

from pcf.allocation import allocation_shares, compare_keys
from pcf.calculator import calculate_pcf
from pcf.scope3 import map_category, scope3_rollup
from pcf.sensitivity import tornado
from pcf.uncertainty import BASIC_UNCERTAINTY, dqr, dqr_label, gsd95, monte_carlo, summarise_samples

BEST = dict(reliability=1, completeness=1, temporal=1, geographical=1, technological=1)


def test_pedigree_gsd():
    assert gsd95(BEST, "material") == pytest.approx(BASIC_UNCERTAINTY["material"])
    worse = {**BEST, "technological": 5}
    assert gsd95(worse, "material") > gsd95(BEST, "material")
    with pytest.raises(ValueError):
        gsd95({**BEST, "temporal": 6}, "material")


def test_dqr_bands():
    assert dqr(BEST) == 1.0 and dqr_label(1.0) == "Excellent"
    assert dqr_label(2.5) == "Good"


def test_monte_carlo_reproducible_and_centred(study):
    r = calculate_pcf(study, "WK-200")
    a, b = monte_carlo(r.inventory, 5000, seed=7), monte_carlo(r.inventory, 5000, seed=7)
    assert np.array_equal(a, b)
    s = summarise_samples(a, r.total)
    assert s["p2_5"] < r.total < s["p97_5"]
    assert s["median"] == pytest.approx(r.total, rel=0.05)


def test_allocation_shares(study):
    for key in ("mass", "units", "economic"):
        assert allocation_shares(study.factory_allocation, key).sum() == pytest.approx(1.0)
    cmp = compare_keys(study.factory_allocation, 1_800_000)
    assert cmp.loc["WK-200", "mass"] > cmp.loc["WK-200", "units"]  # heavy product carries more under mass
    with pytest.raises(ValueError):
        allocation_shares(study.factory_allocation, "volume")


def test_scope3_mapping(study):
    m = study.settings["scope3"]["mapping"]
    assert map_category("distribution", "dc_to_retail", m) == 9
    assert map_category("distribution", "port_to_port", m) == 4
    assert map_category("use", "electricity", m) == 11
    assert map_category("end_of_life", "recycling", m) == 12


def test_scope3_rollup_reconciles(study):
    out = scope3_rollup(study, 2025)
    total = out["by_category"]["tco2e"].sum()
    manual = 0.0
    for _, s in study.units_sold[study.units_sold["year"] == 2025].iterrows():
        r = calculate_pcf(study, s["product_id"], {"use_region": s["region"], "eol_region": s["region"]})
        manual += r.total * s["units"] / 1000
    assert total == pytest.approx(manual)
    assert out["by_category"]["share_pct"].sum() == pytest.approx(100)


def test_tornado_symmetric_for_linear_parameter(study):
    t = tornado(study, "WK-200").set_index("parameter")
    row = t.loc["PCBA emission factor"]
    assert row["low_delta_pct"] == pytest.approx(-row["high_delta_pct"])
    assert t.iloc[0]["swing_kgco2e"] >= t.iloc[-1]["swing_kgco2e"]
