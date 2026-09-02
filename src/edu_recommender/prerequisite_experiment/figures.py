"""Own prerequisite experiment figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import (
    BASELINE_MODEL,
    FIGURE_METADATA,
    MODEL_COLOURS,
    MODEL_LABELS,
    PLANNED_METRICS,
    PRIMARY_K,
    VARIANT_MODEL,
)


def _write_figures(
    summary_rows: list[dict[str, object]],
    profile_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
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
        "figures/prerequisite_experiment_metrics_at_5.png",
        "figures/prerequisite_experiment_paired_ndcg_at_5.png",
        "figures/prerequisite_experiment_diagnostics_at_5.png",
    )
    _plot_metrics(summary_rows, output_dir / files[0])
    _plot_paired_ndcg(profile_rows, output_dir / files[1])
    _plot_diagnostics(diagnostic_rows, output_dir / files[2])
    return files

def _plot_metrics(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = {
        str(row["model"]): row
        for row in rows
        if int(row["k"]) == PRIMARY_K
    }
    labels = ["Precision@5", "Recall@5", "NDCG@5"]
    fields = PLANNED_METRICS
    positions = list(range(len(fields)))
    width = 0.34
    fig, axis = plt.subplots(figsize=(9.5, 5.2))
    for index, model in enumerate((BASELINE_MODEL, VARIANT_MODEL)):
        offset = -width / 2 if index == 0 else width / 2
        values = [float(selected[model][field]) for field in fields]
        bars = axis.bar(
            [position + offset for position in positions],
            values,
            width,
            label=MODEL_LABELS[model],
            color=MODEL_COLOURS[model],
        )
        axis.bar_label(bars, fmt="%.3f", padding=3)
    axis.set_title("Ranking metrics before and after hard prerequisite eligibility")
    axis.set_ylabel("Macro mean across 11 profiles")
    axis.set_xticks(positions, labels)
    axis.set_ylim(0, 1.08)
    axis.grid(axis="y")
    axis.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_paired_ndcg(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    baseline = {
        str(row["profile_id"]): float(row["ndcg_at_k"])
        for row in rows
        if row["model"] == BASELINE_MODEL
        and int(row["k"]) == PRIMARY_K
    }
    variant = {
        str(row["profile_id"]): float(row["ndcg_at_k"])
        for row in rows
        if row["model"] == VARIANT_MODEL
        and int(row["k"]) == PRIMARY_K
    }
    improvements = 0
    ties = 0
    declines = 0
    fig, axis = plt.subplots(figsize=(8.5, 6))
    for profile_id in sorted(baseline):
        before = baseline[profile_id]
        after = variant[profile_id]
        improvements += after > before
        ties += after == before
        declines += after < before
        colour = (
            "#16A34A"
            if after > before
            else "#DC2626"
            if after < before
            else "#A3A3A3"
        )
        axis.plot(
            [0, 1],
            [before, after],
            color=colour,
            alpha=0.7,
            linewidth=1.7,
        )
        axis.scatter(
            [0, 1],
            [before, after],
            color=[
                MODEL_COLOURS[BASELINE_MODEL],
                MODEL_COLOURS[VARIANT_MODEL],
            ],
            s=38,
            zorder=3,
        )
    axis.set_title("Paired profile-level NDCG@5")
    axis.set_ylabel("NDCG@5")
    axis.set_xticks(
        [0, 1],
        [MODEL_LABELS[BASELINE_MODEL], MODEL_LABELS[VARIANT_MODEL]],
    )
    axis.set_ylim(0, 1.04)
    axis.grid(axis="y")
    axis.text(
        0.5,
        0.04,
        f"{improvements} improved, {ties} unchanged, {declines} declined",
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        color="#525252",
    )
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_diagnostics(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = {str(row["model"]): row for row in rows}
    fields = (
        ("skill_gap_coverage", "Skill-gap\ncoverage"),
        ("provider_diversity", "Provider\ndiversity"),
        ("format_diversity", "Format\ndiversity"),
        ("intra_list_diversity", "Intra-list\ndiversity"),
        ("difficulty_match_rate", "Difficulty\nmatch"),
        ("prerequisite_validity_rate", "Prerequisite\nvalidity"),
    )
    positions = list(range(len(fields)))
    width = 0.34
    fig, axis = plt.subplots(figsize=(11.5, 5.6))
    for index, model in enumerate((BASELINE_MODEL, VARIANT_MODEL)):
        offset = -width / 2 if index == 0 else width / 2
        values = [
            float(selected[model][field])
            for field, _ in fields
        ]
        axis.bar(
            [position + offset for position in positions],
            values,
            width,
            label=MODEL_LABELS[model],
            color=MODEL_COLOURS[model],
        )
    axis.set_title("Recommendation-quality diagnostics at K=5")
    axis.set_ylabel("Rate or normalised score")
    axis.set_xticks(positions, [label for _, label in fields])
    axis.set_ylim(0, 1.08)
    axis.grid(axis="y")
    axis.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.25), ncol=2)
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
