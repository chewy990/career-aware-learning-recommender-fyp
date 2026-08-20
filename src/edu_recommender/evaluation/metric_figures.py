"""Own evaluation metric figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import DEFAULT_K_VALUES, MODEL_COLOURS, MODEL_LABELS
from .drawing import _save_figure
from .reporting import _humanise, _models_from_rows


def _plot_metrics_by_k(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    metric_titles = (
        ("precision_at_k", "Precision"),
        ("recall_at_k", "Recall"),
        ("ndcg_at_k", "NDCG"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), sharex=True)
    for axis, (metric, title) in zip(axes, metric_titles):
        for model in _models_from_rows(rows):
            model_rows = sorted(
                (row for row in rows if row["model"] == model),
                key=lambda row: int(row["k"]),
            )
            axis.plot(
                [int(row["k"]) for row in model_rows],
                [float(row[metric]) for row in model_rows],
                marker="o",
                linewidth=2,
                color=MODEL_COLOURS[model],
                label=MODEL_LABELS[model],
            )
        axis.set_title(f"{title}@K")
        axis.set_xlabel("K")
        axis.set_ylim(0, 1.04)
        axis.set_xticks(DEFAULT_K_VALUES)
        axis.grid(axis="y")
    axes[0].set_ylabel("Score")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False)
    fig.suptitle("Model performance across recommendation-list lengths", fontsize=16)
    fig.tight_layout(rect=(0, 0.1, 1, 0.93))
    _save_figure(fig, path)

def _plot_pathway_ndcg(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [row for row in rows if int(row["k"]) == 5]
    pathways = sorted({str(row["pathway"]) for row in selected})
    models = _models_from_rows(selected)
    positions = list(range(len(pathways)))
    width = 0.24
    fig, axis = plt.subplots(figsize=(12.5, 5.8))
    for model_index, model in enumerate(models):
        lookup = {
            str(row["pathway"]): float(row["ndcg_at_k"])
            for row in selected
            if row["model"] == model
        }
        offsets = [
            position + (model_index - (len(models) - 1) / 2) * width
            for position in positions
        ]
        axis.bar(
            offsets,
            [lookup[pathway] for pathway in pathways],
            width=width,
            color=MODEL_COLOURS[model],
            label=MODEL_LABELS[model],
        )
    axis.set_title("NDCG@5 by career pathway")
    axis.set_ylabel("Mean NDCG@5")
    axis.set_ylim(0, 1.05)
    axis.set_xticks(positions, [_humanise(pathway) for pathway in pathways])
    axis.tick_params(axis="x", rotation=18)
    axis.grid(axis="y")
    axis.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.27))
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_profile_ndcg(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [row for row in rows if int(row["k"]) == 5]
    profiles = sorted({str(row["profile_id"]) for row in selected})
    models = _models_from_rows(selected)
    positions = list(range(len(profiles)))
    width = 0.24
    fig, axis = plt.subplots(figsize=(13.5, 5.8))
    for model_index, model in enumerate(models):
        lookup = {
            str(row["profile_id"]): float(row["ndcg_at_k"])
            for row in selected
            if row["model"] == model
        }
        offsets = [
            position + (model_index - (len(models) - 1) / 2) * width
            for position in positions
        ]
        axis.bar(
            offsets,
            [lookup[profile] for profile in profiles],
            width=width,
            color=MODEL_COLOURS[model],
            label=MODEL_LABELS[model],
        )
    axis.set_title("Profile-level NDCG@5 exposes variation hidden by the mean")
    axis.set_ylabel("NDCG@5")
    axis.set_xlabel("Evaluation profile")
    axis.set_ylim(0, 1.05)
    axis.set_xticks(positions, profiles)
    axis.grid(axis="y")
    axis.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout()
    _save_figure(fig, path)
