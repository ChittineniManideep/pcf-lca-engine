"""Emission-factor library: candidate search, applicability scoring and selection.

Every selection is logged with the competing candidates and a plain-language
justification, so dataset choices can be reviewed (ISO 14044 data quality
requirements; ISO 14067).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Weights for the combined applicability score (lower = more applicable)
WEIGHTS = {"geographical": 0.35, "technological": 0.25, "temporal": 0.20, "reliability": 0.10, "completeness": 0.10}

GEO_DESC = {1: "exact match", 2: "parent region", 3: "global average", 4: "different region"}


@dataclass
class Selection:
    ef_id: str
    name: str
    value: float
    unit: str
    category: str
    geography: str
    reference_year: int
    pedigree: dict
    score: float
    reason: str
    candidates: list


class EFLibrary:
    def __init__(self, df: pd.DataFrame, regions: dict, study_year: int):
        self.df = df.copy()
        self.by_id = self.df.set_index("ef_id")
        self.regions = regions
        self.study_year = study_year

    # ---------------------------------------------------------------- scoring
    def ancestors(self, geo: str) -> list[str]:
        chain, cur = [], self.regions.get(geo)
        while cur:
            chain.append(cur)
            cur = self.regions.get(cur)
        if "GLO" not in chain and geo != "GLO":
            chain.append("GLO")
        return chain

    def geo_score(self, origin: str, dataset_geo: str) -> int:
        if dataset_geo == origin:
            return 1
        if dataset_geo == "GLO":
            return 3
        if dataset_geo in self.ancestors(origin):
            return 2
        return 4

    def temporal_score(self, ref_year: int) -> int:
        diff = abs(self.study_year - int(ref_year))
        for limit, score in ((3, 1), (6, 2), (10, 3), (15, 4)):
            if diff <= limit:
                return score
        return 5

    def _pedigree(self, row: pd.Series, origin: str) -> dict:
        return {
            "reliability": int(row["reliability"]),
            "completeness": int(row["completeness"]),
            "temporal": self.temporal_score(row["reference_year"]),
            "geographical": self.geo_score(origin, row["geography"]),
            "technological": int(row["technological"]),
        }

    # -------------------------------------------------------------- selection
    def get(self, ef_id: str) -> pd.Series:
        if ef_id not in self.by_id.index:
            raise KeyError(f"Emission factor {ef_id} not in library")
        return self.by_id.loc[ef_id]

    def pedigree_for(self, ef_id: str, origin: str) -> dict:
        return self._pedigree(self.get(ef_id), origin)

    def candidates(self, material_class: str, technologies: tuple[str, ...] | None = None,
                   unit: str | None = None) -> pd.DataFrame:
        c = self.df[self.df["material_class"] == material_class]
        if technologies:
            c = c[c["technology"].isin(technologies)]
        if unit:
            c = c[c["unit"] == unit]
        return c

    def select(self, material_class: str, origin: str, technologies: tuple[str, ...] | None = None,
               unit: str | None = None) -> Selection:
        cands = self.candidates(material_class, technologies, unit)
        if cands.empty:
            raise LookupError(f"No emission factor for class='{material_class}' tech={technologies} unit={unit}")

        scored = []
        for _, row in cands.iterrows():
            ped = self._pedigree(row, origin)
            score = sum(WEIGHTS[k] * ped[k] for k in WEIGHTS)
            scored.append((score, row, ped))
        scored.sort(key=lambda t: (t[0], t[1]["ef_id"]))
        best_score, best, ped = scored[0]

        reason = (f"{best['ef_id']} ({best['geography']}, {int(best['reference_year'])}) for {material_class} "
                  f"sourced in {origin}: geography {GEO_DESC[ped['geographical']]}, "
                  f"temporal score {ped['temporal']}, technology score {ped['technological']}")
        if len(scored) > 1:
            runner = scored[1]
            reason += f"; preferred over {runner[1]['ef_id']} ({runner[0]:.2f} vs {best_score:.2f})"

        return Selection(
            ef_id=best["ef_id"], name=best["name"], value=float(best["value_kgco2e"]), unit=best["unit"],
            category=best["category"], geography=best["geography"], reference_year=int(best["reference_year"]),
            pedigree=ped, score=round(best_score, 3), reason=reason,
            candidates=[{"ef_id": r["ef_id"], "score": round(s, 3), **p} for s, r, p in scored],
        )
