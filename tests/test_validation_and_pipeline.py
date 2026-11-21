import json

import pandas as pd
import pytest

from pcf.pipeline import ValidationError, run
from pcf.validation import validate_product, validate_study


def status(checks, name):
    return next(c.status for c in checks if c.check == name)


def test_clean_inputs_have_no_failures(study):
    df = validate_study(study)
    assert not (df["status"] == "FAIL").any(), df[df["status"] == "FAIL"]


def test_mass_balance_failure_detected(fresh_study):
    fresh_study.boms["WM-100"].loc[fresh_study.boms["WM-100"]["component_id"] == "C01", "mass_g"] = 40.0
    assert status(validate_product(fresh_study, "WM-100"), "mass balance: product") == "FAIL"


def test_unmapped_material_detected(fresh_study):
    bom = fresh_study.boms["WM-100"]
    bom.loc[bom["component_id"] == "C03", "material_class"] = "graphene"
    checks = validate_product(fresh_study, "WM-100")
    assert status(checks, "every material mapped to an emission factor") == "FAIL"
    assert status(checks, "every material has an end-of-life group") == "FAIL"


def test_bad_values_detected(fresh_study):
    bom = fresh_study.boms["WK-200"]
    bom.loc[bom["component_id"] == "C02", "recycled_content_pct"] = 130
    bom.loc[bom["component_id"] == "C03", "qty"] = 0
    checks = validate_product(fresh_study, "WK-200")
    assert status(checks, "recycled content 0-100%") == "FAIL"
    assert status(checks, "positive mass and quantity") == "FAIL"


def test_cutoff_rule(fresh_study):
    bom = fresh_study.boms["WM-100"]
    bom.loc[bom["component_id"] == "X01", "mass_g"] = 5.0
    assert status(validate_product(fresh_study, "WM-100"), "cut-off: excluded mass share") == "FAIL"


def test_pipeline_blocks_on_invalid_input(fresh_study, tmp_path):
    fresh_study.ef_library.loc[0, "value_kgco2e"] = -1
    with pytest.raises(ValidationError):
        run(fresh_study, tmp_path, mc_runs=200, log=lambda *_: None)


def test_pipeline_end_to_end(study, tmp_path):
    run(study, tmp_path, mc_runs=500, log=lambda *_: None)
    summary = pd.read_csv(tmp_path / "pcf_summary.csv")
    assert set(summary["product_id"]) == {"WM-100", "WK-200"}
    pact = json.loads((tmp_path / "WM-100" / "pact_footprint.json").read_text())
    assert pact["pcf"]["pCfExcludingBiogenic"] == pytest.approx(summary.set_index("product_id").loc["WM-100", "total_kgco2e"], abs=1e-3)
    assert "ISO Standard 14067" in pact["pcf"]["crossSectoralStandardsUsed"]
    report = (tmp_path / "WK-200" / "PCF_report.md").read_text()
    for section in ("Goal and scope", "Hotspots", "Interpretation", "Biogenic"):
        assert section in report
    for f in ("inventory.csv", "ef_selection_log.csv", "tornado.png", "monte_carlo.png"):
        assert (tmp_path / "WK-200" / f).exists()


def test_sql_layer_reconciles(study, tmp_path):
    duckdb = pytest.importorskip("duckdb")  # noqa: F841
    import importlib.util
    from pathlib import Path

    run(study, tmp_path, mc_runs=200, log=lambda *_: None)
    spec = importlib.util.spec_from_file_location("sqlrun", Path(__file__).parents[1] / "scripts" / "run_sql_local.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    con = mod.build(warehouse=tmp_path / "warehouse")
    kpi = con.execute("SELECT product_id, pcf_kgco2e FROM v_pcf_kpis").df().set_index("product_id")
    summary = pd.read_csv(tmp_path / "pcf_summary.csv").set_index("product_id")
    for pid in summary.index:
        assert float(kpi.loc[pid, "pcf_kgco2e"]) == pytest.approx(summary.loc[pid, "total_kgco2e"], abs=1e-3)
    s3_sql = con.execute("SELECT SUM(tco2e) FROM v_scope3_by_category").fetchone()[0]
    s3_py = pd.read_csv(tmp_path / "scope3_by_category.csv")["tco2e"].sum()
    assert float(s3_sql) == pytest.approx(s3_py, rel=1e-6)
