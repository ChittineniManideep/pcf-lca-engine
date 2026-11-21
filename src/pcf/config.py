"""Load study configuration, product definitions and input data into one object."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BOOL_COLS = ("is_packaging", "excluded")


def _read_bom(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"component_id": str})
    for col in BOOL_COLS:
        df[col] = df[col].astype(str).str.strip().str.lower().map({"true": True, "false": False})
    df["notes"] = df["notes"].fillna("")
    return df


@dataclass
class Study:
    root: Path
    settings: dict
    products: dict[str, dict]
    boms: dict[str, pd.DataFrame]
    ef_library: pd.DataFrame
    process_energy: pd.DataFrame
    factory_allocation: pd.DataFrame
    supplier_pcf: pd.DataFrame
    units_sold: pd.DataFrame
    scenarios: dict = field(default_factory=dict)

    # convenience accessors -------------------------------------------------
    @property
    def reference_year(self) -> int:
        return int(self.settings["study"]["reference_year"])

    @property
    def regions(self) -> dict:
        return self.settings["regions"]

    def copy(self) -> Study:
        return Study(
            root=self.root,
            settings=copy.deepcopy(self.settings),
            products=copy.deepcopy(self.products),
            boms={k: v.copy() for k, v in self.boms.items()},
            ef_library=self.ef_library.copy(),
            process_energy=self.process_energy.copy(),
            factory_allocation=self.factory_allocation.copy(),
            supplier_pcf=self.supplier_pcf.copy(),
            units_sold=self.units_sold.copy(),
            scenarios=copy.deepcopy(self.scenarios),
        )


def load_study(root: Path | str | None = None) -> Study:
    root = Path(root) if root else PROJECT_ROOT
    settings = yaml.safe_load((root / "config" / "study.yaml").read_text())
    scenarios_path = root / "config" / "scenarios.yaml"
    scenarios = yaml.safe_load(scenarios_path.read_text())["scenarios"] if scenarios_path.exists() else {}

    products, boms = {}, {}
    for path in sorted((root / "products").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text())
        pid = cfg["product_id"]
        products[pid] = cfg
        boms[pid] = _read_bom(root / "data" / "bom" / f"{pid}.csv")

    return Study(
        root=root,
        settings=settings,
        products=products,
        boms=boms,
        ef_library=pd.read_csv(root / "data" / "emission_factors" / "ef_library.csv"),
        process_energy=pd.read_csv(root / "data" / "activity" / "process_energy.csv").set_index("process"),
        factory_allocation=pd.read_csv(root / "data" / "activity" / "factory_allocation.csv"),
        supplier_pcf=pd.read_csv(root / "data" / "suppliers" / "supplier_pcf.csv", dtype={"component_id": str}),
        units_sold=pd.read_csv(root / "data" / "sales" / "units_sold.csv"),
        scenarios=scenarios,
    )


def _set_path(d: dict, dotted: str, value) -> None:
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def apply_scenario(study: Study, name: str) -> Study:
    """Return a copy of the study with a named eco-design scenario applied."""
    if name not in study.scenarios:
        raise KeyError(f"Unknown scenario '{name}'. Available: {sorted(study.scenarios)}")
    s = study.copy()
    for ch in s.scenarios[name].get("changes", []):
        targets = list(s.products) if ch["product"] == "*" else [ch["product"]]
        for pid in targets:
            if ch["type"] == "bom":
                bom = s.boms[pid]
                bom.loc[bom["component_id"] == ch["component"], ch["field"]] = ch["value"]
            elif ch["type"] == "bom_class":
                bom = s.boms[pid]
                bom.loc[bom["material_class"] == ch["material_class"], ch["field"]] = ch["value"]
            elif ch["type"] == "product":
                _set_path(s.products[pid], ch["path"], ch["value"])
            else:
                raise ValueError(f"Unknown scenario change type: {ch['type']}")
    return s
