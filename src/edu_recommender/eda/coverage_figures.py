"""Own eda coverage figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from .contracts import PATHWAY_ORDER
from .drawing import _blend_color, _draw_wrapped_centered, _save_png
from .tables import _label


def _plot_coverage_heatmap(image_tools, rows, path: Path) -> None:
    Image, ImageDraw, PngImagePlugin, fonts = image_tools
    skills = sorted({str(row["skill"]) for row in rows})
    lookup = {
        (str(row["skill"]), str(row["pathway"])): int(
            row["resources_covering_skill"]
        )
        for row in rows
    }
    max_value = max(lookup.values())
    width, height = 1600, 1120
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 300, 70, 190, 85
    cell_width = (width - left - right) / len(PATHWAY_ORDER)
    cell_height = (height - top - bottom) / len(skills)
    draw.text(
        (55, 40),
        "Resources covering each required pathway skill",
        fill="#171717",
        font=fonts["title"],
    )
    draw.text(
        (55, 92),
        "Cells show resource counts; dash means the skill is not required.",
        fill="#525252",
        font=fonts["small"],
    )
    for column_index, pathway in enumerate(PATHWAY_ORDER):
        center_x = left + cell_width * (column_index + 0.5)
        _draw_wrapped_centered(
            draw,
            (center_x, top - 70),
            _label(pathway),
            fonts["small"],
            "#404040",
        )
    for row_index, skill in enumerate(skills):
        center_y = top + cell_height * (row_index + 0.5)
        draw.text(
            (left - 18, center_y),
            _label(skill),
            fill="#262626",
            font=fonts["small"],
            anchor="rm",
        )
        for column_index, pathway in enumerate(PATHWAY_ORDER):
            x1 = left + cell_width * column_index
            y1 = top + cell_height * row_index
            value = lookup.get((skill, pathway))
            if value is None:
                fill = "#F5F5F5"
                text = "-"
                text_color = "#737373"
            else:
                ratio = value / max_value
                fill = _blend_color("#F3E8FF", "#6D28D9", ratio)
                text = str(value)
                text_color = "white" if ratio > 0.55 else "#171717"
            draw.rectangle(
                (x1, y1, x1 + cell_width, y1 + cell_height),
                fill=fill,
                outline="#FFFFFF",
                width=2,
            )
            draw.text(
                (x1 + cell_width / 2, y1 + cell_height / 2),
                text,
                fill=text_color,
                font=fonts["small"],
                anchor="mm",
            )
    _save_png(image, path, PngImagePlugin)
