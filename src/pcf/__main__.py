"""Command-line interface.

    python -m pcf run                       # full pipeline -> reports/
    python -m pcf run --scenario combined   # run with an eco-design scenario applied
    python -m pcf validate                  # input validation only (exit 1 on FAIL)
    python -m pcf calc WM-100               # quick stage breakdown for one product
    python -m pcf select PCBA CN            # show EF candidates and applicability scores
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .calculator import calculate_pcf
from .config import load_study
from .ef_library import EFLibrary
from .pipeline import ValidationError, run
from .validation import validate_study


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="pcf", description="ISO 14067 product carbon footprint engine")
    p.add_argument("--root", default=None, help="project root (default: repository root)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run the full pipeline")
    r.add_argument("--out", default="reports")
    r.add_argument("--scenario", default="baseline")
    r.add_argument("--mc-runs", type=int, default=10_000)
    r.add_argument("--year", type=int, default=2025)

    sub.add_parser("validate", help="validate inputs")
    c = sub.add_parser("calc", help="calculate one product")
    c.add_argument("product_id")
    c.add_argument("--use-region", default=None)
    s = sub.add_parser("select", help="explain emission-factor selection")
    s.add_argument("material_class")
    s.add_argument("origin")
    s.add_argument("--tech", nargs="*", default=None)

    a = p.parse_args(argv)
    study = load_study(a.root)
    pd.set_option("display.width", 160)

    if a.cmd == "run":
        out = Path(a.out) if Path(a.out).is_absolute() else study.root / a.out
        if a.scenario != "baseline":
            out = out / f"scenario_{a.scenario}"
        try:
            run(study, out, a.scenario, a.mc_runs, a.year)
        except ValidationError as e:
            print(e, file=sys.stderr)
            return 1
        print(f"Reports written to {out}")
    elif a.cmd == "validate":
        df = validate_study(study)
        print(df.to_string(index=False))
        return 1 if (df["status"] == "FAIL").any() else 0
    elif a.cmd == "calc":
        res = calculate_pcf(study, a.product_id, {"use_region": a.use_region} if a.use_region else None)
        print(res.by_stage.round(4).to_string())
        print(f"TOTAL  {res.total:.4f} kg CO2e   PDS {res.primary_data_share:.1f}%   DQR {res.dqr:.2f}")
    elif a.cmd == "select":
        lib = EFLibrary(study.ef_library, study.regions, study.reference_year)
        sel = lib.select(a.material_class, a.origin, tuple(a.tech) if a.tech else None)
        print(sel.reason)
        print(pd.DataFrame(sel.candidates).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
