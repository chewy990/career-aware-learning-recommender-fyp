"""Own eda figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from .coverage_figures import _plot_coverage_heatmap
from .distribution_figures import _plot_horizontal, _plot_pathways, _plot_vertical
from .drawing import _load_fonts
from .tables import _dimension_rows, _label


def _write_figures(
    tables: dict[str, list[dict[str, object]]],
    output_dir: Path,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    except ImportError as error:
        raise RuntimeError(
            "Phase 2 EDA requires Pillow to generate report figures."
        ) from error

    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    fonts = _load_fonts(ImageFont)
    image_tools = (Image, ImageDraw, PngImagePlugin, fonts)

    distributions = tables["resource_distribution.csv"]
    _plot_pathways(
        image_tools,
        _dimension_rows(distributions, "pathway_positive_relevance"),
        _dimension_rows(distributions, "pathway_core_relevance"),
        figures_dir / "resources_by_pathway.png",
    )
    _plot_horizontal(
        image_tools,
        _dimension_rows(distributions, "provider"),
        "Resources by provider",
        "Resource count",
        figures_dir / "resources_by_provider.png",
    )
    _plot_horizontal(
        image_tools,
        _dimension_rows(distributions, "format"),
        "Resources by format",
        "Resource count",
        figures_dir / "resources_by_format.png",
    )
    _plot_vertical(
        image_tools,
        _dimension_rows(distributions, "difficulty"),
        "Resources by difficulty",
        "Difficulty",
        figures_dir / "resources_by_difficulty.png",
    )
    _plot_vertical(
        image_tools,
        _dimension_rows(distributions, "duration_band"),
        "Resource duration distribution",
        "Duration band",
        figures_dir / "resource_duration_distribution.png",
    )
    _plot_vertical(
        image_tools,
        _dimension_rows(distributions, "cost"),
        "Resources by cost",
        "Cost",
        figures_dir / "resources_by_cost.png",
    )
    _plot_horizontal(
        image_tools,
        [
            {
                "category": _label(str(row["skill"])),
                "count": row["resource_count"],
            }
            for row in tables["skill_frequency.csv"]
        ],
        "Resource coverage by skill",
        "Resource count",
        figures_dir / "skill_frequency.png",
    )
    _plot_horizontal(
        image_tools,
        [
            {
                "category": (
                    f"{_label(str(row['skill_a']))} + "
                    f"{_label(str(row['skill_b']))}"
                ),
                "count": row["resource_count"],
            }
            for row in tables["skill_cooccurrence.csv"][:10]
        ],
        "Top 10 skill co-occurrences",
        "Resource count",
        figures_dir / "skill_cooccurrence.png",
    )
    _plot_coverage_heatmap(
        image_tools,
        tables["pathway_skill_coverage.csv"],
        figures_dir / "pathway_skill_coverage.png",
    )
    _plot_vertical(
        image_tools,
        _dimension_rows(tables["profile_distribution.csv"], "target_pathway"),
        "Evaluation profiles by pathway",
        "Target pathway",
        figures_dir / "profiles_by_pathway.png",
    )
    _plot_vertical(
        image_tools,
        [
            {
                "category": str(row["profile_id"]),
                "count": row["relevant_count"],
            }
            for row in tables["relevance_summary.csv"]
        ],
        "Relevant resources by evaluation profile",
        "Profile ID",
        figures_dir / "relevance_by_profile.png",
    )
