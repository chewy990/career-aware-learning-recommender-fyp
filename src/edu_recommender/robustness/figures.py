"""Own robustness figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import (
    COMPONENTS,
    FIGURE_METADATA,
    MODEL_COLOUR,
    NEGATIVE_COLOUR,
    NEUTRAL_COLOUR,
    POSITIVE_COLOUR,
)
from .reporting import _humanise


def _write_figures(
    ablation_rows: list[dict[str, object]],
    sensitivity_rows: list[dict[str, object]],
    seeded_rows: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
    output_dir: Path,
) -> tuple[str, ...]:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.edgecolor": "#737373",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": "#E5E5E5",
            "grid.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    files = (
        "figures/phase4_ablation_ndcg_at_5.png",
        "figures/phase4_weight_sensitivity_ndcg_at_5.png",
        "figures/phase4_seeded_configurations_ndcg_at_5.png",
        "figures/phase4_failure_cases.png",
    )
    _plot_ablation(ablation_rows, output_dir / files[0])
    _plot_sensitivity(sensitivity_rows, output_dir / files[1])
    _plot_seeded(seeded_rows, output_dir / files[2])
    _plot_failures(failure_rows, output_dir / files[3])
    return files

def _plot_ablation(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [
        row
        for row in rows
        if int(row["k"]) == 5 and row["removed_component"]
    ]
    selected.sort(key=lambda row: float(row["delta_ndcg"]))
    labels = [
        _humanise(str(row["removed_component"]))
        for row in selected
    ]
    values = [float(row["delta_ndcg"]) for row in selected]
    colours = [
        NEGATIVE_COLOUR if value < 0 else POSITIVE_COLOUR
        for value in values
    ]
    fig, axis = plt.subplots(figsize=(10.5, 6.2))
    axis.barh(labels, values, color=colours)
    axis.axvline(0, color="#404040", linewidth=1)
    axis.set_title("Change in NDCG@5 after removing one hybrid component")
    axis.set_xlabel("NDCG@5 change from full hybrid")
    axis.set_xlim(min(values) - 0.008, max(values) + 0.008)
    axis.grid(axis="x")
    for index, value in enumerate(values):
        axis.text(
            value + (0.001 if value >= 0 else -0.001),
            index,
            f"{value:+.4f}",
            va="center",
            ha="left" if value >= 0 else "right",
        )
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_sensitivity(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [row for row in rows if int(row["k"]) == 5]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7.2), sharex=True, sharey=True)
    baseline = next(
        float(row["ndcg_at_k"])
        for row in selected
        if row["component"] == COMPONENTS[0]
        and float(row["multiplier"]) == 1.0
    )
    for axis, component in zip(axes.flat, COMPONENTS):
        component_rows = sorted(
            (
                row
                for row in selected
                if row["component"] == component
            ),
            key=lambda row: float(row["multiplier"]),
        )
        axis.plot(
            [float(row["multiplier"]) for row in component_rows],
            [float(row["ndcg_at_k"]) for row in component_rows],
            color=MODEL_COLOUR,
            marker="o",
            linewidth=2,
        )
        axis.axhline(
            baseline,
            color=NEUTRAL_COLOUR,
            linestyle="--",
            linewidth=1,
        )
        axis.set_title(_humanise(component))
        axis.grid(axis="y")
    for axis in axes[-1]:
        axis.set_xlabel("Weight multiplier")
    for axis in axes[:, 0]:
        axis.set_ylabel("NDCG@5")
    fig.suptitle("One-at-a-time hybrid weight sensitivity", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save_figure(fig, path)

def _plot_seeded(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [
        row for row in rows if int(row["k"]) == 5
    ]
    baseline = next(
        float(row["ndcg_at_k"])
        for row in selected
        if row["configuration_id"] == "S000_baseline"
    )
    alternatives = [
        row
        for row in selected
        if row["configuration_id"] != "S000_baseline"
    ]
    fig, axis = plt.subplots(figsize=(11.5, 5.4))
    axis.scatter(
        range(1, len(alternatives) + 1),
        [float(row["ndcg_at_k"]) for row in alternatives],
        color=MODEL_COLOUR,
        s=65,
        zorder=3,
    )
    axis.axhline(
        baseline,
        color="#111111",
        linestyle="--",
        label=f"Baseline {baseline:.4f}",
    )
    axis.set_title("Seeded bounded weight configurations at K=5")
    axis.set_xlabel("Pre-seeded configuration")
    axis.set_ylabel("NDCG@5")
    axis.set_xticks(
        range(1, len(alternatives) + 1),
        [str(row["configuration_id"]) for row in alternatives],
        rotation=45,
    )
    axis.grid(axis="y")
    axis.legend(frameon=False)
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_failures(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    counts = Counter(str(row["failure_type"]) for row in rows)
    labels = sorted(counts)
    values = [counts[label] for label in labels]
    fig, axis = plt.subplots(figsize=(10.5, 5.8))
    axis.bar(
        [_humanise(label) for label in labels],
        values,
        color=MODEL_COLOUR,
    )
    axis.set_title("Flagged hybrid failure cases at K=5")
    axis.set_ylabel("Case count")
    axis.tick_params(axis="x", rotation=22)
    axis.grid(axis="y")
    for index, value in enumerate(values):
        axis.text(index, value + 0.1, str(value), ha="center")
    fig.tight_layout()
    _save_figure(fig, path)

def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
        metadata=FIGURE_METADATA,
    )
    plt.close(fig)
