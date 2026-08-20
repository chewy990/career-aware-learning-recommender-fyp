"""Own eda distribution figures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path

from .contracts import PATHWAY_ORDER
from .drawing import (
    _draw_centered,
    _draw_rotated_label,
    _draw_wrapped_centered,
    _save_png,
)
from .tables import _chart_label, _label


def _plot_horizontal(image_tools, rows, title: str, x_label: str, path: Path) -> None:
    Image, ImageDraw, PngImagePlugin, fonts = image_tools
    labels = [_chart_label(str(row["category"])) for row in rows]
    values = [int(row["count"]) for row in rows]
    width = 1500
    height = max(720, 180 + 54 * len(rows))
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 360, 90, 130, 105
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(values) if values else 1

    draw.text((55, 40), title, fill="#171717", font=fonts["title"])
    for tick in range(6):
        value = round(max_value * tick / 5)
        x = left + chart_width * tick / 5
        draw.line((x, top, x, top + chart_height), fill="#E5E5E5", width=2)
        _draw_centered(
            draw,
            (x, top + chart_height + 14),
            str(value),
            fonts["small"],
            "#525252",
            anchor="ma",
        )

    row_height = chart_height / max(len(rows), 1)
    bar_height = min(30, row_height * 0.58)
    for index, (label, value) in enumerate(zip(labels, values)):
        center_y = top + row_height * (index + 0.5)
        draw.text(
            (left - 18, center_y),
            label,
            fill="#262626",
            font=fonts["body"],
            anchor="rm",
        )
        bar_width = chart_width * value / max_value
        draw.rounded_rectangle(
            (
                left,
                center_y - bar_height / 2,
                left + bar_width,
                center_y + bar_height / 2,
            ),
            radius=5,
            fill="#6D28D9",
        )
        draw.text(
            (left + bar_width + 10, center_y),
            str(value),
            fill="#171717",
            font=fonts["body"],
            anchor="lm",
        )
    draw.line(
        (left, top + chart_height, left + chart_width, top + chart_height),
        fill="#737373",
        width=2,
    )
    _draw_centered(
        draw,
        (left + chart_width / 2, height - 45),
        x_label,
        fonts["axis"],
        "#404040",
        anchor="mm",
    )
    _save_png(image, path, PngImagePlugin)

def _plot_vertical(image_tools, rows, title: str, x_label: str, path: Path) -> None:
    Image, ImageDraw, PngImagePlugin, fonts = image_tools
    labels = [_chart_label(str(row["category"])) for row in rows]
    values = [int(row["count"]) for row in rows]
    width, height = 1500, 850
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 120, 70, 130, 205
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(values) if values else 1

    draw.text((55, 40), title, fill="#171717", font=fonts["title"])
    for tick in range(6):
        value = round(max_value * tick / 5)
        y = top + chart_height - chart_height * tick / 5
        draw.line((left, y, left + chart_width, y), fill="#E5E5E5", width=2)
        draw.text(
            (left - 16, y),
            str(value),
            fill="#525252",
            font=fonts["small"],
            anchor="rm",
        )

    slot_width = chart_width / max(len(rows), 1)
    bar_width = min(115, slot_width * 0.58)
    for index, (label, value) in enumerate(zip(labels, values)):
        center_x = left + slot_width * (index + 0.5)
        bar_height = chart_height * value / max_value
        draw.rounded_rectangle(
            (
                center_x - bar_width / 2,
                top + chart_height - bar_height,
                center_x + bar_width / 2,
                top + chart_height,
            ),
            radius=5,
            fill="#6D28D9",
        )
        draw.text(
            (center_x, top + chart_height - bar_height - 10),
            str(value),
            fill="#171717",
            font=fonts["body"],
            anchor="ms",
        )
        _draw_wrapped_centered(
            draw,
            (center_x, top + chart_height + 18),
            label,
            fonts["small"],
            "#404040",
        )
    draw.line(
        (left, top + chart_height, left + chart_width, top + chart_height),
        fill="#737373",
        width=2,
    )
    _draw_centered(
        draw,
        (left + chart_width / 2, height - 42),
        x_label,
        fonts["axis"],
        "#404040",
        anchor="mm",
    )
    _draw_rotated_label(
        Image,
        ImageDraw,
        image,
        "Count",
        fonts["axis"],
        (36, top + chart_height / 2),
    )
    _save_png(image, path, PngImagePlugin)

def _plot_pathways(image_tools, positive_rows, core_rows, path: Path) -> None:
    Image, ImageDraw, PngImagePlugin, fonts = image_tools
    positive_by_pathway = {
        str(row["category"]): int(row["count"]) for row in positive_rows
    }
    core_by_pathway = {
        str(row["category"]): int(row["count"]) for row in core_rows
    }
    labels = [_label(pathway) for pathway in PATHWAY_ORDER]
    positive_values = [positive_by_pathway[pathway] for pathway in PATHWAY_ORDER]
    core_values = [core_by_pathway[pathway] for pathway in PATHWAY_ORDER]
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 130, 80, 170, 215
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(positive_values)

    draw.text(
        (55, 40),
        "Resource relevance coverage by pathway",
        fill="#171717",
        font=fonts["title"],
    )
    draw.rectangle((55, 104, 82, 131), fill="#6D28D9")
    draw.text(
        (94, 117),
        "Positive relevance (1-3)",
        fill="#404040",
        font=fonts["small"],
        anchor="lm",
    )
    draw.rectangle((360, 104, 387, 131), fill="#A3A3A3")
    draw.text(
        (399, 117),
        "Core relevance (3)",
        fill="#404040",
        font=fonts["small"],
        anchor="lm",
    )
    for tick in range(6):
        value = round(max_value * tick / 5)
        y = top + chart_height - chart_height * tick / 5
        draw.line((left, y, left + chart_width, y), fill="#E5E5E5", width=2)
        draw.text(
            (left - 16, y),
            str(value),
            fill="#525252",
            font=fonts["small"],
            anchor="rm",
        )
    slot_width = chart_width / len(PATHWAY_ORDER)
    bar_width = min(72, slot_width * 0.28)
    for index, label in enumerate(labels):
        center_x = left + slot_width * (index + 0.5)
        for value, color, offset in (
            (positive_values[index], "#6D28D9", -bar_width * 0.58),
            (core_values[index], "#A3A3A3", bar_width * 0.58),
        ):
            bar_height = chart_height * value / max_value
            x1 = center_x + offset - bar_width / 2
            x2 = center_x + offset + bar_width / 2
            draw.rounded_rectangle(
                (x1, top + chart_height - bar_height, x2, top + chart_height),
                radius=4,
                fill=color,
            )
            draw.text(
                ((x1 + x2) / 2, top + chart_height - bar_height - 9),
                str(value),
                fill="#171717",
                font=fonts["small"],
                anchor="ms",
            )
        _draw_wrapped_centered(
            draw,
            (center_x, top + chart_height + 18),
            label,
            fonts["small"],
            "#404040",
        )
    _draw_centered(
        draw,
        (left + chart_width / 2, height - 42),
        "Pathway",
        fonts["axis"],
        "#404040",
        anchor="mm",
    )
    _draw_rotated_label(
        Image,
        ImageDraw,
        image,
        "Resource count (overlapping)",
        fonts["axis"],
        (36, top + chart_height / 2),
    )
    _save_png(image, path, PngImagePlugin)
