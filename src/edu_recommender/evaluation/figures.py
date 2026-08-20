"""Own evaluation figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .diagnostic_figures import _plot_diagnostics, _plot_uncertainty
from .metric_figures import _plot_metrics_by_k, _plot_pathway_ndcg, _plot_profile_ndcg


def _write_evaluation_figures(
    summary_rows: list[dict[str, object]],
    profile_rows: list[dict[str, object]],
    pathway_rows: list[dict[str, object]],
    uncertainty_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
    output_dir: Path,
) -> tuple[str, ...]:
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
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
        "figures/phase3_metrics_by_k.png",
        "figures/phase3_pathway_ndcg_at_5.png",
        "figures/phase3_profile_ndcg_at_5.png",
        "figures/phase3_uncertainty_ndcg_at_5.png",
        "figures/phase3_diagnostics_at_5.png",
    )
    _plot_metrics_by_k(summary_rows, output_dir / files[0])
    _plot_pathway_ndcg(pathway_rows, output_dir / files[1])
    _plot_profile_ndcg(profile_rows, output_dir / files[2])
    _plot_uncertainty(uncertainty_rows, output_dir / files[3])
    _plot_diagnostics(diagnostic_rows, output_dir / files[4])
    return files

