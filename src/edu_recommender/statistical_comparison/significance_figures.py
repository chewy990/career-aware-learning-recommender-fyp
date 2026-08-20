"""Own statistical comparison significance figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import BASELINE_MODELS, METRICS, MODEL_LABELS
from .drawing import _save_figure
from .reporting import _metric_short


def _plot_adjusted_p_values(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    columns = [
        f"{_metric_short(metric)}@{k}"
        for metric in METRICS
        for k in (3, 5, 10)
    ]
    matrix = []
    for baseline in BASELINE_MODELS:
        values = []
        for metric in METRICS:
            for k in (3, 5, 10):
                row = next(
                    item
                    for item in rows
                    if item["baseline_model"] == baseline
                    and item["metric"] == metric
                    and int(item["k"]) == k
                )
                values.append(
                    float(row["exact_permutation_holm_p"])
                )
        matrix.append(values)
    fig, axis = plt.subplots(figsize=(12.5, 3.8))
    image = axis.imshow(
        matrix,
        cmap="Purples_r",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axis.set_title("Holm-adjusted exact permutation p-values")
    axis.set_xticks(range(len(columns)), columns, rotation=35, ha="right")
    axis.set_yticks(
        range(len(BASELINE_MODELS)),
        [f"Hybrid vs {MODEL_LABELS[model]}" for model in BASELINE_MODELS],
    )
    for row_index, values in enumerate(matrix):
        for column_index, value in enumerate(values):
            axis.text(
                column_index,
                row_index,
                f"{value:.3f}",
                ha="center",
                va="center",
                color="white" if value < 0.45 else "#111111",
            )
    fig.colorbar(image, ax=axis, label="Adjusted p-value")
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_win_tie_loss(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [row for row in rows if int(row["k"]) == 5]
    labels = [
        f"{_metric_short(str(row['metric']))}\nvs {MODEL_LABELS[str(row['baseline_model'])]}"
        for row in selected
    ]
    wins = [int(row["hybrid_wins"]) for row in selected]
    ties = [int(row["ties"]) for row in selected]
    losses = [int(row["hybrid_losses"]) for row in selected]
    positions = list(range(len(selected)))
    fig, axis = plt.subplots(figsize=(12, 5.6))
    axis.bar(positions, wins, color="#16A34A", label="Hybrid wins")
    axis.bar(
        positions,
        ties,
        bottom=wins,
        color="#A3A3A3",
        label="Ties",
    )
    axis.bar(
        positions,
        losses,
        bottom=[
            win + tie for win, tie in zip(wins, ties)
        ],
        color="#DC2626",
        label="Hybrid losses",
    )
    axis.set_title("Profile-level wins, ties, and losses at K=5")
    axis.set_ylabel("Profiles")
    axis.set_xticks(positions, labels)
    axis.set_ylim(0, 11.5)
    axis.grid(axis="y")
    axis.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.25))
    fig.tight_layout()
    _save_figure(fig, path)
