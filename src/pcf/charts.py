"""Static charts for the study reports (matplotlib, PNG)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .calculator import STAGE_LABELS, STAGES  # noqa: E402

# Categorical slots in fixed order (validated default palette, light mode)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.titlelocation": "left", "figure.dpi": 150, "savefig.bbox": "tight",
})


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def stage_contribution(results: dict, path: Path):
    pids = list(results)
    fig, ax = plt.subplots(figsize=(8, 1.2 + 0.7 * len(pids)))
    left = np.zeros(len(pids))
    for i, stage in enumerate(STAGES):
        vals = np.array([results[p].by_stage[stage] / results[p].total * 100 for p in pids])
        ax.barh(pids, vals, left=left, color=SERIES[i], edgecolor="white", linewidth=2, label=STAGE_LABELS[stage],
                height=0.55)
        for j, v in enumerate(vals):
            if v >= 8:
                ax.text(left[j] + v / 2, j, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9)
        left += vals
    for j, p in enumerate(pids):
        ax.text(101, j, f"{results[p].total:.2f} kg CO2e", va="center", color=INK, fontsize=9)
    ax.set_xlim(0, 118)
    ax.set_xlabel("Share of cradle-to-grave PCF (%)")
    ax.set_title("PCF by life-cycle stage")
    ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.45, -0.35), frameon=False, fontsize=8.5)
    ax.invert_yaxis()
    _save(fig, path)


def hotspots(result, path: Path, n: int = 10):
    h = result.hotspots(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(h) + 1))
    ax.barh(h["hotspot"], h["kgco2e"], color=SERIES[0], height=0.6)
    for i, (v, s) in enumerate(zip(h["kgco2e"], h["share_pct"])):
        ax.text(v, i, f"  {v:.2f} ({s:.0f}%)", va="center", color=INK, fontsize=8.5)
    ax.set_xlim(0, h["kgco2e"].max() * 1.3)
    ax.set_xlabel("kg CO2e per declared unit")
    ax.set_title(f"{result.product_id} — top {n} hotspots")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    _save(fig, path)


def tornado(df: pd.DataFrame, path: Path):
    d = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(d) + 1.2))
    y = np.arange(len(d))
    ax.barh(y, d["low_delta_pct"], color=SERIES[0], height=0.55, label="Parameter −20%")
    ax.barh(y, d["high_delta_pct"], color=SERIES[1], height=0.55, label="Parameter +20%")
    ax.set_yticks(y, d["parameter"])
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.set_xlabel("Change in total PCF (%)")
    ax.set_title(f"{d['product_id'].iloc[0]} — sensitivity (±20%, one at a time)")
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    _save(fig, path)


def monte_carlo(samples: np.ndarray, summary: dict, pid: str, path: Path):
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.hist(samples, bins=60, color=SERIES[0], alpha=0.85, edgecolor="white", linewidth=0.5)
    for x, ls, lab in ((summary["deterministic"], "-", "Deterministic"), (summary["p2_5"], "--", "95% interval"),
                       (summary["p97_5"], "--", None)):
        ax.axvline(x, color=INK, linestyle=ls, linewidth=1.2, label=lab)
    ax.set_xlabel("kg CO2e per declared unit")
    ax.set_ylabel("Iterations")
    ax.set_title(f"{pid} — Monte Carlo ({len(samples):,} runs): {summary['p2_5']:.2f}–{summary['p97_5']:.2f} kg CO2e")
    ax.legend(frameon=False, fontsize=8.5)
    _save(fig, path)


def scope3_categories(by_cat: pd.DataFrame, path: Path):
    d = by_cat.sort_values("tco2e")
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(d) + 1.2))
    ax.barh(d["category_name"], d["tco2e"], color=SERIES[0], height=0.6)
    for i, (v, s) in enumerate(zip(d["tco2e"], d["share_pct"])):
        ax.text(v, i, f"  {v:,.0f} t ({s:.0f}%)", va="center", color=INK, fontsize=8.5)
    ax.set_xlim(0, d["tco2e"].max() * 1.3)
    ax.set_xlabel("t CO2e (FY units sold)")
    ax.set_title("Scope 3 emissions from the two product lines, by category")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    _save(fig, path)


def scenarios(df: pd.DataFrame, path: Path):
    d = df[df["scenario"] != "baseline"]
    names = list(dict.fromkeys(d["scenario"]))
    pids = list(dict.fromkeys(d["product_id"]))
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(names) + 1.4))
    y = np.arange(len(names))
    h = 0.36
    for i, pid in enumerate(pids):
        vals = [d[(d["scenario"] == n) & (d["product_id"] == pid)]["change_vs_baseline_pct"].iloc[0] for n in names]
        ax.barh(y + (i - 0.5) * h, vals, height=h - 0.04, color=SERIES[i], label=pid)
        for yy, v in zip(y + (i - 0.5) * h, vals):
            ax.text(v, yy, f"{v:.1f}%  " if v < 0 else (f"  +{v:.1f}%" if v > 0.05 else "  0%"), va="center", ha="right" if v < 0 else "left",
                    color=INK, fontsize=8)
    ax.set_yticks(y, [n.replace("_", " ") for n in names])
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.set_xlabel("Change vs baseline PCF (%)")
    ax.set_title("Eco-design scenarios")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.invert_yaxis()
    ax.set_xlim(min(d["change_vs_baseline_pct"].min() * 1.25, -1), 2)
    _save(fig, path)
