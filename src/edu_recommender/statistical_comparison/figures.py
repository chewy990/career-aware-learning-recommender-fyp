"""Own statistical comparison figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .paired_figures import _plot_mean_differences, _plot_paired_ndcg
from .significance_figures import _plot_adjusted_p_values, _plot_win_tie_loss


def _write_figures(
    difference_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
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
        "figures/phase5_paired_ndcg_at_5.png",
        "figures/phase5_mean_differences.png",
        "figures/phase5_holm_adjusted_p_values.png",
        "figures/phase5_win_tie_loss_at_5.png",
    )
    _plot_paired_ndcg(difference_rows, output_dir / files[0])
    _plot_mean_differences(comparison_rows, output_dir / files[1])
    _plot_adjusted_p_values(comparison_rows, output_dir / files[2])
    _plot_win_tie_loss(comparison_rows, output_dir / files[3])
    return files

