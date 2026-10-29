"""Generate the Nakitce heart and lira icons using Pillow."""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
STORE = ROOT / "store" / "assets"


def _curve(points: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    result = []
    for step in range(65):
        t = step / 64
        u = 1 - t
        result.append(
            (
                u**3 * points[0][0] + 3 * u**2 * t * points[1][0]
                + 3 * u * t**2 * points[2][0] + t**3 * points[3][0],
                u**3 * points[0][1] + 3 * u**2 * t * points[1][1]
                + 3 * u * t**2 * points[2][1] + t**3 * points[3][1],
            )
        )
    return result


def _gradient(
    size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]
) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(image)
    for y in range(size):
        color = tuple(round(a + (b - a) * y / (size - 1)) for a, b in zip(top, bottom))
        draw.line((0, y, size - 1, y), fill=color + (255,))
    return image


def create_nakitce_icon(
    size: int = 1024,
    output_path: str | Path = ASSETS / "icon.png",
    *,
    rounded: bool = True,
) -> Path:
    if size < 32:
        raise ValueError("Icon size must be at least 32 pixels.")
    scale = size * 2
    image = _gradient(scale, (13, 71, 161), (0, 180, 180))
    curves = (
        ((0.50, 0.32), (0.39, 0.13), (0.16, 0.20), (0.16, 0.39)),
        ((0.16, 0.39), (0.16, 0.56), (0.36, 0.70), (0.50, 0.83)),
        ((0.50, 0.83), (0.64, 0.70), (0.84, 0.56), (0.84, 0.39)),
        ((0.84, 0.39), (0.84, 0.20), (0.61, 0.13), (0.50, 0.32)),
    )
    outline = [
        (x * scale, y * scale)
        for curve in curves
        for x, y in _curve(curve)
    ]
    heart = Image.new("L", image.size, 0)
    ImageDraw.Draw(heart).polygon(outline, fill=255)

    shadow = Image.new("L", image.size, 0)
    ImageDraw.Draw(shadow).polygon(
        [(x, y + scale * 0.025) for x, y in outline], fill=110
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(scale * 0.025))
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer.putalpha(shadow)
    image = Image.alpha_composite(image, layer)

    red = _gradient(scale, (255, 98, 101), (175, 15, 38))
    red.putalpha(heart)
    image = Image.alpha_composite(image, red)
    highlight = Image.new("L", image.size, 0)
    ImageDraw.Draw(highlight).ellipse(
        (scale * 0.21, scale * 0.24, scale * 0.44, scale * 0.37), fill=85
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(scale * 0.035))
    sheen = Image.new("RGBA", image.size, (255, 255, 255, 0))
    sheen.putalpha(ImageChops.multiply(highlight, heart))
    image = Image.alpha_composite(image, sheen)

    # Bundled font keeps the lira glyph identical on Windows and Linux.
    font = ImageFont.truetype(str(ASSETS / "fonts" / "DejaVuSans.ttf"), round(scale * 0.36))
    glyph = "\u20ba"
    left, top, right, bottom = font.getbbox(glyph)
    x = scale * 0.5 - (left + right) / 2
    y = scale * 0.505 - (top + bottom) / 2
    text_shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(text_shadow).text(
        (x + scale * 0.009, y + scale * 0.012), glyph, font=font,
        fill=(70, 10, 10, 180), stroke_width=max(1, round(scale * 0.002)),
    )
    image = Image.alpha_composite(
        image, text_shadow.filter(ImageFilter.GaussianBlur(scale * 0.004))
    )
    draw = ImageDraw.Draw(image)
    stroke = max(1, round(scale * 0.002))
    for offset in range(round(scale * 0.006), 0, -1):
        draw.text(
            (x + offset, y + offset), glyph, font=font, fill="#B87708",
            stroke_width=stroke, stroke_fill="#B87708",
        )
    draw.text(
        (x, y), glyph, font=font, fill="#FFC107",
        stroke_width=stroke, stroke_fill="#FFC107",
    )
    if rounded:
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, scale - 1, scale - 1), radius=round(scale * 0.22), fill=255
        )
        image.putalpha(mask)
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG")
    return output


def export_icons() -> Path:
    create_nakitce_icon()
    return create_nakitce_icon(512, STORE / "icon_512.png", rounded=False)


if __name__ == "__main__":
    store_icon = export_icons()
    print(f"Wrote {ASSETS / 'icon.png'}")
    print(f"Wrote {store_icon}")
