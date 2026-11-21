"""Data-quality scoring (pedigree matrix) and Monte Carlo uncertainty propagation.

Pedigree uncertainty factors follow the ecoinvent v2 / Weidema & Wesnaes (1996)
approach: each indicator score (1 = best, 5 = worst) maps to an uncertainty factor U,
and the 95% geometric standard deviation of a lognormal distribution is

    GSD95 = exp( sqrt( ln(Ub)^2 + sum_i ln(U_i)^2 ) )

where Ub is the basic uncertainty of the flow type.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

PEDIGREE_INDICATORS = ("reliability", "completeness", "temporal", "geographical", "technological")

UNCERTAINTY_FACTORS = {
    "reliability": (1.00, 1.05, 1.10, 1.20, 1.50),
    "completeness": (1.00, 1.02, 1.05, 1.10, 1.20),
    "temporal": (1.00, 1.03, 1.10, 1.20, 1.50),
    "geographical": (1.00, 1.01, 1.02, 1.05, 1.10),
    "technological": (1.00, 1.05, 1.20, 1.50, 2.00),
}

BASIC_UNCERTAINTY = {
    "material": 1.05,
    "component": 1.10,
    "energy": 1.05,
    "transport": 2.00,
    "eol": 1.50,
    "spend": 1.50,
    "primary": 1.05,
}

# PEF-style DQR bands
DQR_BANDS = [(1.6, "Excellent"), (2.0, "Very good"), (3.0, "Good"), (4.0, "Fair"), (5.01, "Poor")]


def gsd95(pedigree: dict, category: str) -> float:
    ub = BASIC_UNCERTAINTY.get(category, 1.10)
    s = math.log(ub) ** 2
    for ind in PEDIGREE_INDICATORS:
        score = int(pedigree[ind])
        if not 1 <= score <= 5:
            raise ValueError(f"Pedigree score for {ind} must be 1-5, got {score}")
        s += math.log(UNCERTAINTY_FACTORS[ind][score - 1]) ** 2
    return math.exp(math.sqrt(s))


def dqr(pedigree: dict) -> float:
    return float(np.mean([pedigree[i] for i in PEDIGREE_INDICATORS]))


def dqr_label(score: float) -> str:
    for upper, label in DQR_BANDS:
        if score <= upper:
            return label
    return "Poor"


def weighted_dqr(inventory: pd.DataFrame) -> float:
    w = inventory["kgco2e"].clip(lower=0)
    return float((inventory["dqr"] * w).sum() / w.sum())


def monte_carlo(inventory: pd.DataFrame, n: int = 10_000, seed: int = 42) -> np.ndarray:
    """Propagate emission-factor uncertainty; returns n samples of the total (kg CO2e).

    Each inventory line is lognormal with median = deterministic value and
    sigma = ln(GSD95) / 2. Lines are sampled independently (no correlation).
    """
    rng = np.random.default_rng(seed)
    det = inventory["kgco2e"].to_numpy(dtype=float)
    sigma = np.log(inventory["gsd95"].to_numpy(dtype=float)) / 2.0
    z = rng.standard_normal((n, len(det)))
    samples = det * np.exp(sigma * z)
    return samples.sum(axis=1)


def summarise_samples(samples: np.ndarray, deterministic: float) -> dict:
    p = np.percentile(samples, [2.5, 50, 97.5])
    return {
        "deterministic": deterministic,
        "mean": float(samples.mean()),
        "p2_5": float(p[0]),
        "median": float(p[1]),
        "p97_5": float(p[2]),
        "cv_pct": float(samples.std() / samples.mean() * 100),
    }
