"""Own statistical comparison paired figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import BASELINE_MODELS, METRICS, MODEL_COLOURS, MODEL_LABELS
from .drawing import _save_figure
from .reporting import _metric_label


def _plot_paired_ndcg(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [
        row
        for row in rows
        if row["metric"] == "ndcg_at_k" and int(row["k"]) == 5
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.8), sharey=True)
    for axis, baseline in zip(axes, BASELINE_MODELS):
        baseline_rows = [
            row
            for row in selected
            if row["baseline_model"] == baseline
        ]
        for row in baseline_rows:
            baseline_value = float(row["baseline_value"])
            hybrid_value = float(row["hybrid_value"])
            colour = "#16A34A" if hybrid_value > baseline_value else (
                "#DC2626" if hybrid_value < baseline_value else "#A3A3A3"
            )
            axis.plot(
                [0, 1],
                [baseline_value, hybrid_value],
                color=colour,
                alpha=0.65,
                linewidth=1.5,
            )
            axis.scatter(
                [0, 1],
                [baseline_value, hybrid_value],
                color=[
                    MODEL_COLOURS[baseline],
                    MODEL_COLOURS["hybrid"],
                ],
                s=35,
                zorder=3,
            )
        axis.set_title(
            f"Hybrid vs {MODEL_LABELS[baseline]}"
        )
        axis.set_xticks(
            [0, 1],
            [MODEL_LABELS[baseline], "Hybrid"],
        )
        axis.set_ylim(0, 1.04)
        axis.grid(axis="y")
    axes[0].set_ylabel("Profile NDCG@5")
    fig.suptitle("Paired profile-level NDCG@5 comparisons", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save_figure(fig, path)

def _plot_mean_differences(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=False)
    for axis, metric in zip(axes, METRICS):
        metric_rows = [row for row in rows if row["metric"] == metric]
        for baseline in BASELINE_MODELS:
            baseline_rows = sorted(
                (
                    row
                    for row in metric_rows
                    if row["baseline_model"] == baseline
                ),
                key=lambda row: int(row["k"]),
            )
            x_values = [
                int(row["k"])
                + (-0.12 if baseline == "popularity" else 0.12)
                for row in baseline_rows
            ]
            means = [
                float(row["mean_difference"])
                for row in baseline_rows
            ]
            lower_errors = [
                value - float(row["ci_95_lower"])
                for value, row in zip(means, baseline_rows)
            ]
            upper_errors = [
                float(row["ci_95_upper"]) - value
                for value, row in zip(means, baseline_rows)
            ]
            axis.errorbar(
                x_values,
                means,
                yerr=[lower_errors, upper_errors],
                fmt="o",
                capsize=5,
                color=MODEL_COLOURS[baseline],
                label=f"vs {MODEL_LABELS[baseline]}",
            )
        axis.axhline(0, color="#404040", linewidth=1)
        axis.set_title(_metric_label(metric))
        axis.set_xlabel("K")
        axis.set_xticks([3, 5, 10])
        axis.grid(axis="y")
    axes[0].set_ylabel("Hybrid minus baseline mean")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Paired mean differences with bootstrap 95% intervals", fontsize=16)
    fig.tight_layout(rect=(0, 0.12, 1, 0.93))
    _save_figure(fig, path)
