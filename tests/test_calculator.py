import pytest

from pcf.calculator import STAGES, calculate_pcf
from pcf.config import apply_scenario


@pytest.mark.parametrize("pid", ["WM-100", "WK-200"])
def test_total_equals_sum_of_stages_and_lines(study, pid):
    r = calculate_pcf(study, pid)
    assert r.total == pytest.approx(r.by_stage.sum())
    assert r.total == pytest.approx((r.inventory["activity_amount"] * r.inventory["ef_value"]).sum())
    assert set(r.inventory["stage"]) <= set(STAGES)
    assert (r.inventory["kgco2e"] >= 0).all()


def test_regression_baseline(study):
    """Guards against silent changes in data or method."""
    assert calculate_pcf(study, "WM-100").total == pytest.approx(2.794, abs=0.005)
    assert calculate_pcf(study, "WK-200").total == pytest.approx(12.186, abs=0.005)


def test_supplier_primary_data_rules(study):
    r = calculate_pcf(study, "WM-100")
    d = r.supplier_decisions.set_index("component_id")
    assert d.loc["C08", "decision"] == "accepted"
    pcba = r.inventory[r.inventory["component_id"] == "C08"]
    assert len(pcba) == 1 and pcba["data_type"].iloc[0] == "primary"
    assert pcba["kgco2e"].iloc[0] == pytest.approx(0.88)

    k = calculate_pcf(study, "WK-200").supplier_decisions.set_index("component_id")
    assert k.loc["C08", "decision"] == "rejected" and "older" in k.loc["C08", "reason"]
    assert k.loc["C02", "decision"] == "rejected" and "boundary" in k.loc["C02", "reason"]


def test_recycled_content_blending(study):
    r = calculate_pcf(study, "WM-100")
    top = r.inventory[(r.inventory["component_id"] == "C01") & (r.inventory["sub_stage"] == "materials")].iloc[0]
    assert top["ef_value"] == pytest.approx(0.5 * 5.65 + 0.5 * 1.40)
    assert "@50%" in top["ef_id"]


def test_scrap_increases_gross_input(study):
    r = calculate_pcf(study, "WK-200")
    case = r.inventory[(r.inventory["component_id"] == "C01") & (r.inventory["sub_stage"] == "materials")].iloc[0]
    assert case["activity_amount"] == pytest.approx(0.180 / (1 - 0.15))


def test_excluded_lines_not_in_inventory(study):
    r = calculate_pcf(study, "WM-100")
    assert not r.inventory["component_id"].isin(["X01", "X02"]).any()


def test_air_freight_drives_distribution(study):
    base = calculate_pcf(study, "WM-100").by_stage["distribution"]
    s = apply_scenario(study, "no_air_freight")
    assert calculate_pcf(s, "WM-100").by_stage["distribution"] < base


def test_renewable_override_only_hits_assembly_and_overhead(study):
    s = apply_scenario(study, "renewable_assembly")
    r = calculate_pcf(s, "WM-100")
    prod = r.inventory[r.inventory["stage"] == "production"]
    assert set(prod[prod["sub_stage"].isin(["final_assembly", "factory_overhead"])]["ef_id"]) == {"EF-ELEC-CN-SOLAR"}
    assert set(prod[prod["sub_stage"] == "component_processing"]["ef_id"]) == {"EF-ELEC-CN"}


def test_use_region_changes_use_phase(study):
    eu = calculate_pcf(study, "WM-100", {"use_region": "RER"}).by_stage["use"]
    us = calculate_pcf(study, "WM-100", {"use_region": "RNA"}).by_stage["use"]
    assert us / eu == pytest.approx(0.370 / 0.255, rel=1e-6)


def test_biogenic_reported_separately_and_balances(study):
    r = calculate_pcf(study, "WM-100")
    b = r.biogenic
    assert not b.empty
    balance = (b["removal_kgco2"] + b["eol_release_kgco2"] + b["stored_in_landfill_kgco2"]
               + b["transferred_to_recycling_kgco2"]).sum()
    assert balance == pytest.approx(0.0, abs=1e-9)
    assert "biogenic" not in " ".join(r.inventory["item"]).lower()


def test_eol_mass_conserved(study):
    r = calculate_pcf(study, "WK-200")
    eol_kg = r.inventory.loc[r.inventory["stage"] == "end_of_life", "activity_amount"].sum()
    assert eol_kg == pytest.approx(r.meta["product_kg"] + r.meta["packaging_kg"])


def test_unknown_product(study):
    with pytest.raises(KeyError):
        calculate_pcf(study, "NOPE")
