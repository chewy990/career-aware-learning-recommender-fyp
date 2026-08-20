"""Own evaluation diagnostic figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import MODEL_COLOURS, MODEL_LABELS
from .drawing import _save_figure
from .reporting import _models_from_rows


def _plot_uncertainty(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [
        row
        for row in rows
        if int(row["k"]) == 5 and row["metric"] == "ndcg_at_k"
    ]
    models = _models_from_rows(selected)
    means = [
        float(next(row["mean"] for row in selected if row["model"] == model))
        for model in models
    ]
    lowers = [
        float(next(row["ci_95_lower"] for row in selected if row["model"] == model))
        for model in models
    ]
    uppers = [
        float(next(row["ci_95_upper"] for row in selected if row["model"] == model))
        for model in models
    ]
    fig, axis = plt.subplots(figsize=(8.5, 5.3))
    for index, model in enumerate(models):
        axis.errorbar(
            index,
            means[index],
            yerr=[
                [means[index] - lowers[index]],
                [uppers[index] - means[index]],
            ],
            fmt="o",
            markersize=9,
            capsize=7,
            linewidth=2,
            color=MODEL_COLOURS[model],
        )
    axis.set_title("Profile-bootstrap 95% intervals for NDCG@5")
    axis.set_ylabel("Mean NDCG@5")
    axis.set_ylim(0, 1.04)
    axis.set_xticks(range(len(models)), [MODEL_LABELS[model] for model in models])
    axis.grid(axis="y")
    fig.tight_layout()
    _save_figure(fig, path)

def _plot_diagnostics(
    rows: list[dict[str, object]],
    path: Path,
) -> None:
    selected = [row for row in rows if int(row["k"]) == 5]
    models = _models_from_rows(selected)
    diagnostics = (
        ("catalogue_coverage", "Catalogue\ncoverage"),
        ("skill_gap_coverage", "Skill-gap\ncoverage"),
        ("provider_diversity", "Provider\ndiversity"),
        ("format_diversity", "Format\ndiversity"),
        ("intra_list_diversity", "Intra-list\ndiversity"),
        ("difficulty_match_rate", "Difficulty\nmatch"),
        ("prerequisite_validity_rate", "Prerequisite\nvalidity"),
    )
    positions = list(range(len(diagnostics)))
    width = 0.24
    fig, axis = plt.subplots(figsize=(13.5, 6.0))
    for model_index, model in enumerate(models):
        row = next(item for item in selected if item["model"] == model)
        offsets = [
            position + (model_index - (len(models) - 1) / 2) * width
            for position in positions
        ]
        axis.bar(
            offsets,
            [float(row[field]) for field, _ in diagnostics],
            width=width,
            color=MODEL_COLOURS[model],
            label=MODEL_LABELS[model],
        )
    axis.set_title("Recommendation-quality diagnostics at K=5")
    axis.set_ylabel("Rate or normalised score")
    axis.set_ylim(0, 1.05)
    axis.set_xticks(positions, [label for _, label in diagnostics])
    axis.grid(axis="y")
    axis.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.24))
    fig.tight_layout()
    _save_figure(fig, path)
