"""Export Play Console raster assets from brand colors (no external SVG deps)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generate_icon import export_icons

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
STORE = ROOT / "store" / "assets"

NAVY = (11, 28, 44, 255)
TEAL = (54, 214, 178, 255)
TEAL_DARK = (18, 148, 125, 255)
WHITE = (246, 252, 249, 255)
MUTED = (214, 231, 229, 255)


def _font(size: int):
    for name in ("segoeuib.ttf", "SegoeUI-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def export_icon():
    return export_icons()


def export_feature_graphic():
    STORE.mkdir(parents=True, exist_ok=True)
    with Image.open(ASSETS / "icon.png") as source:
        mark = source.convert("RGBA")
    w, h = 1024, 500
    img = Image.new("RGBA", (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(NAVY[:3], (15, 76, 69)))
        draw.line((0, y, w - 1, y), fill=color + (255,))
    accents = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(accents)
    draw.ellipse((-80, 280, 340, 700), fill=(54, 214, 178, 28))
    draw.ellipse((780, -120, 1160, 260), fill=(54, 214, 178, 28))
    img = Image.alpha_composite(img, accents)
    draw = ImageDraw.Draw(img)

    img.alpha_composite(mark.resize((84, 84), Image.Resampling.LANCZOS), (64, 70))

    title = _font(54)
    sub = _font(36)
    line = _font(22)
    small = _font(18)
    draw.text((168, 78), "Nakitçe", font=title, fill=WHITE)
    draw.text((66, 180), "Esnafın cep defteri", font=sub, fill=WHITE)
    draw.text((66, 240), "Aldım · Verdim · Veresiye · WhatsApp ekstre", font=line, fill=TEAL)
    draw.text((66, 310), "Paranı doğru yönet, kârını gör", font=small, fill=MUTED)

    # phone mock
    draw.rounded_rectangle((646, 28, 952, 482), radius=34, fill=(246, 248, 247, 255))
    draw.rounded_rectangle((659, 42, 939, 468), radius=26, fill=(242, 246, 245, 255))
    draw.rounded_rectangle((659, 42, 939, 112), radius=26, fill=WHITE)
    img.alpha_composite(mark.resize((42, 42), Image.Resampling.LANCZOS), (676, 56))
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


def export_screenshots():
    from generate_play_screenshots import export_screenshots as _export

    return _export()


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    icon = export_icon()
    feature = export_feature_graphic()
    shots = export_screenshots()
    print(f"Wrote {icon}")
    print(f"Wrote {feature}")
    for path in shots:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
