import pytest

from pcf.ef_library import EFLibrary
from pcf.units import g_to_kg, gross_input, tonne_km


def test_unit_conversions():
    assert g_to_kg(1500) == 1.5
    assert tonne_km(500, 200) == pytest.approx(100)  # 0.5 t x 200 km
    assert gross_input(0.97, 0.03) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        gross_input(1.0, 1.0)


@pytest.fixture
def lib(study):
    return EFLibrary(study.ef_library, study.regions, study.reference_year)


def test_geo_scores(lib):
    assert lib.geo_score("CN", "CN") == 1
    assert lib.geo_score("CN", "RAS") == 2
    assert lib.geo_score("CN", "GLO") == 3
    assert lib.geo_score("CN", "RER") == 4
    assert lib.geo_score("IE", "RER") == 2


def test_temporal_scores(lib):
    assert lib.temporal_score(2025) == 1
    assert lib.temporal_score(2020) == 2
    assert lib.temporal_score(2017) == 3
    assert lib.temporal_score(2005) == 5


def test_prefers_regional_dataset(lib):
    sel = lib.select("aluminium", "CN", ("virgin", "generic"), "kg")
    assert sel.ef_id == "EF-AL-CN-V"
    sel = lib.select("aluminium", "DE", ("virgin", "generic"), "kg")
    assert sel.ef_id == "EF-AL-GLO-V"  # no EU dataset -> global
    assert "preferred over" in sel.reason


def test_grid_lookup_falls_back_to_region(lib):
    assert lib.select("electricity", "CN", ("grid_mix",), "kWh").ef_id == "EF-ELEC-CN"
    assert lib.select("electricity", "DE", ("grid_mix",), "kWh").ef_id == "EF-ELEC-RER"
    assert lib.select("electricity", "US", ("grid_mix",), "kWh").ef_id == "EF-ELEC-RNA"


def test_unit_filter_and_missing(lib):
    assert lib.select("sensor_module", "TW", None, "unit").unit == "unit"
    with pytest.raises(LookupError):
        lib.select("unobtainium", "CN")
