"""Export Play Console raster assets from brand colors (no external SVG deps)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
STORE = ROOT / "store" / "assets"

NAVY = (11, 28, 44, 255)
TEAL = (54, 214, 178, 255)
TEAL_DARK = (18, 148, 125, 255)
GOLD = (246, 185, 74, 255)
WHITE = (246, 252, 249, 255)
MUTED = (214, 231, 229, 255)


def _font(size: int):
    for name in ("segoeuib.ttf", "SegoeUI-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_mark(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=TEAL)
    inner = int(r * 0.78)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), outline=WHITE, width=max(3, r // 12))
    stroke = max(3, r // 9)
    draw.line((cx, cy - int(r * 0.45), cx, cy + int(r * 0.45)), fill=NAVY[:3], width=stroke)
    draw.arc(
        (cx - int(r * 0.35), cy - int(r * 0.2), cx + int(r * 0.45), cy + int(r * 0.35)),
        start=200,
        end=340,
        fill=NAVY[:3],
        width=stroke,
    )


def export_icon():
    size = 512
    img = Image.new("RGBA", (size, size), NAVY)
    draw = ImageDraw.Draw(img)
    # rounded app-icon feel
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=112, fill=255)
    base = Image.new("RGBA", (size, size), NAVY)
    img = Image.composite(base, Image.new("RGBA", (size, size), (0, 0, 0, 0)), mask)
    draw = ImageDraw.Draw(img)
    _draw_mark(draw, 256, 256, 148)
    draw.ellipse((346, 116, 414, 184), fill=GOLD)
    out = STORE / "icon_512.png"
    img.save(out, "PNG")
    # also keep a copy next to SVG for Flet packaging convenience
    img.save(ASSETS / "icon.png", "PNG")
    return out


def export_feature_graphic():
    w, h = 1024, 500
    img = Image.new("RGBA", (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    draw.ellipse((-80, 280, 340, 700), fill=(54, 214, 178, 28))
    draw.ellipse((780, -120, 1160, 260), fill=(54, 214, 178, 28))

    # mark tile
    draw.rounded_rectangle((64, 70, 136, 142), radius=22, fill=TEAL)
    _draw_mark(draw, 100, 106, 28)

    title = _font(54)
    sub = _font(36)
    line = _font(26)
    small = _font(18)
    draw.text((158, 78), "Nakitçe", font=title, fill=WHITE)
    draw.text((66, 180), "Esnafın cep defteri", font=sub, fill=WHITE)
    draw.text((66, 240), "Kasa · veresiye · stok · tek yerde", font=line, fill=TEAL)
    draw.text((66, 310), "Gelir, gider ve alacaklarını sade tut", font=small, fill=MUTED)

    # phone mock
    draw.rounded_rectangle((646, 28, 952, 482), radius=34, fill=(246, 248, 247, 255))
    draw.rounded_rectangle((659, 42, 939, 468), radius=26, fill=(242, 246, 245, 255))
    draw.rounded_rectangle((659, 42, 939, 112), radius=26, fill=WHITE)
    draw.rounded_rectangle((676, 58, 714, 96), radius=12, fill=TEAL_DARK)
    _draw_mark(draw, 695, 77, 12)
    # mini pie
    cx, cy, r = 799, 220, 70
    draw.pieslice((cx - r, cy - r, cx + r, cy + r), start=-90, end=150, fill=TEAL)
    draw.pieslice((cx - r, cy - r, cx + r, cy + r), start=150, end=270, fill=(228, 88, 78, 255))
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=WHITE)
    draw.rounded_rectangle((676, 320, 792, 372), radius=14, fill=(255, 242, 220, 255))
    draw.rounded_rectangle((806, 320, 922, 372), radius=14, fill=(234, 240, 255, 255))
    draw.rounded_rectangle((676, 396, 922, 436), radius=14, fill=TEAL_DARK)

    out = STORE / "play_feature_graphic.png"
    img.convert("RGB").save(out, "PNG")
    img.convert("RGB").save(ASSETS / "play_feature_graphic.png", "PNG")
    return out


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    icon = export_icon()
    feature = export_feature_graphic()
    print(f"Wrote {icon}")
    print(f"Wrote {feature}")


if __name__ == "__main__":
    main()
