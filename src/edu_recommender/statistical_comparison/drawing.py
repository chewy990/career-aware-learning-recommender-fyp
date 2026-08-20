"""Own the shared Matplotlib save primitive for statistical figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .contracts import FIGURE_METADATA


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
        metadata=FIGURE_METADATA,
    )
    plt.close(fig)
