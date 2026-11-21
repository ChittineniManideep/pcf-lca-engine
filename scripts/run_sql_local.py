"""Load the warehouse extracts into DuckDB and run the reporting views locally.

    python scripts/run_sql_local.py            # prints each view
    python scripts/run_sql_local.py --db pcf.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["dim_product", "dim_emission_factor", "fact_pcf_inventory", "fact_unit_inventory_by_region", "fact_units_sold"]
VIEWS = ["v_pcf_kpis", "v_pcf_by_stage", "v_scope3_by_category", "v_scope3_by_product_region",
         "v_data_quality_priorities", "v_ef_usage"]


def build(db: str = ":memory:", warehouse: Path = ROOT / "reports" / "warehouse") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db)
    con.execute((ROOT / "sql" / "01_schema.sql").read_text())
    for t in TABLES:
        cols = [r[0] for r in con.execute(f"DESCRIBE {t}").fetchall()]
        con.execute(f"INSERT INTO {t} SELECT {', '.join(cols)} FROM read_csv_auto(?, header=true, all_varchar=true)",
                    [str(warehouse / f"{t}.csv")])
    con.execute((ROOT / "sql" / "02_views.sql").read_text())
    return con


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=":memory:")
    a = ap.parse_args()
    con = build(a.db)
    for v in VIEWS:
        print(f"\n== {v} ==")
        print(con.execute(f"SELECT * FROM {v}").df().round(3).to_string(index=False))


if __name__ == "__main__":
    main()
