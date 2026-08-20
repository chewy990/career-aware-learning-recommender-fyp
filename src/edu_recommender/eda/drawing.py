"""Own eda drawing responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from pathlib import Path


def _load_fonts(ImageFont):
    font_dir = Path("C:/Windows/Fonts")
    regular = font_dir / "segoeui.ttf"
    semibold = font_dir / "seguisb.ttf"
    bold = font_dir / "segoeuib.ttf"
    try:
        return {
            "title": ImageFont.truetype(str(bold), 38),
            "axis": ImageFont.truetype(str(semibold), 23),
            "body": ImageFont.truetype(str(regular), 22),
            "small": ImageFont.truetype(str(regular), 19),
        }
    except OSError:
        fallback = ImageFont.load_default()
        return {
            "title": fallback,
            "axis": fallback,
            "body": fallback,
            "small": fallback,
        }

def _draw_centered(draw, position, text, font, color, anchor: str) -> None:
    draw.text(position, text, fill=color, font=font, anchor=anchor)

def _draw_wrapped_centered(draw, position, text, font, color) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= 17 or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    draw.multiline_text(
        position,
        "\n".join(lines),
        fill=color,
        font=font,
        anchor="ma",
        align="center",
        spacing=3,
    )

def _draw_rotated_label(Image, ImageDraw, image, text, font, position) -> None:
    layer = Image.new("RGBA", (460, 70), (255, 255, 255, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.text(
        (230, 35),
        text,
        fill="#404040",
        font=font,
        anchor="mm",
    )
    rotated = layer.rotate(90, expand=True)
    image.paste(
        rotated,
        (
            int(position[0] - rotated.width / 2),
            int(position[1] - rotated.height / 2),
        ),
        rotated,
    )

def _blend_color(start: str, end: str, ratio: float) -> str:
    start_rgb = tuple(int(start[index : index + 2], 16) for index in (1, 3, 5))
    end_rgb = tuple(int(end[index : index + 2], 16) for index in (1, 3, 5))
    blended = tuple(
        round(start_value + (end_value - start_value) * ratio)
        for start_value, end_value in zip(start_rgb, end_rgb)
    )
    return "#" + "".join(f"{value:02X}" for value in blended)

def _save_png(image, path: Path, PngImagePlugin) -> None:
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Software", "Career-aware recommender Phase 2 EDA")
    image.save(path, format="PNG", pnginfo=metadata, optimize=False)
