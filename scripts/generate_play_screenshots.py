"""Play Console telefon ekran görüntüleri (1080×1920, markaya sadık UI mock).

Gerçek cihaz görüntüsü yerine depo içinde tutarlı mağaza varlıkları üretir.
Play en az 2 telefon görüntüsü ister — bu betik 5 adet yazar.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
STORE = ROOT / "store" / "assets" / "screenshots"

W, H = 1080, 1920
NAVY = (11, 28, 44)
TEAL = (15, 155, 130)
TEAL_SOFT = (232, 247, 242)
CANVAS = (238, 243, 242)
INK = (14, 36, 51)
MUTED = (91, 115, 130)
WHITE = (255, 255, 255)
RED = (214, 69, 69)
AMBER = (255, 241, 216)
GOLD = (166, 106, 8)
CARD = (255, 255, 255)
BORDER = (228, 236, 233)


def _font(size: int, bold: bool = False):
    names = (
        ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")
        if bold
        else ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
    )
    bundled = ROOT / "src" / "assets" / "fonts" / "DejaVuSans.ttf"
    candidates = list(names) + ([str(bundled)] if bundled.exists() else [])
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _round_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text(draw, xy, text, font, fill=INK):
    draw.text(xy, text, font=font, fill=fill)


def _phone_chrome(img: Image.Image) -> ImageDraw.ImageDraw:
    draw = ImageDraw.Draw(img)
    # status bar
    draw.rectangle((0, 0, W, 64), fill=WHITE)
    _text(draw, (40, 18), "09:41", _font(28, True), INK)
    _text(draw, (W - 200, 18), "●●● 4G", _font(24), MUTED)
    # header
    draw.rectangle((0, 64, W, 180), fill=WHITE)
    icon_path = ASSETS / "icon.png"
    if icon_path.exists():
        with Image.open(icon_path) as icon:
            mark = icon.convert("RGBA").resize((72, 72), Image.Resampling.LANCZOS)
        img.alpha_composite(mark, (36, 88))
    _text(draw, (128, 92), "Nakitçe", _font(40, True), INK)
    _text(draw, (128, 140), "Ticaretin kalbi", _font(22), MUTED)
    _round_rect(draw, (W - 280, 108, W - 36, 156), 999, TEAL_SOFT)
    _text(draw, (W - 262, 116), "Cebindeki kasa", _font(22, True), TEAL)
    return draw


def _nav(draw, active: str):
    tabs = [("Özet", "home"), ("Hareket", "ledger"), ("Veresiye", "customers"), ("Stok", "inventory"), ("Araçlar", "tools")]
    y0 = H - 150
    draw.rectangle((0, y0, W, H), fill=WHITE)
    slot = W // len(tabs)
    for i, (label, key) in enumerate(tabs):
        x = i * slot
        selected = key == active
        if selected:
            _round_rect(draw, (x + 12, y0 + 18, x + slot - 12, H - 24), 22, TEAL)
        color = WHITE if selected else MUTED
        _text(draw, (x + slot // 2 - 40, y0 + 48), label, _font(24, True), color)


def _caption_banner(draw, title: str, subtitle: str):
    """Üstte mağaza için kısa caption şeridi (ekranın parçası gibi)."""
    _round_rect(draw, (36, 200, W - 36, 320), 28, NAVY)
    _text(draw, (60, 222), title, _font(36, True), WHITE)
    _text(draw, (60, 272), subtitle, _font(24), (158, 217, 203))


def shot_home() -> Image.Image:
    img = Image.new("RGBA", (W, H), CANVAS + (255,))
    draw = _phone_chrome(img)
    _caption_banner(draw, "Aldım / Verdim", "Defter gibi kayıt — jargonsuz")
    y = 348
    # hero
    _round_rect(draw, (36, y, W - 36, y + 340), 36, NAVY)
    _text(draw, (64, y + 36), "Cebindeki kasa defteri", _font(24, True), (158, 217, 203))
    _text(draw, (64, y + 80), "Butik / perakende", _font(48, True), WHITE)
    _text(draw, (64, y + 148), "Miraş Bakkal", _font(28), (215, 245, 238))
    _round_rect(draw, (64, y + 220, 280, y + 300), 20, TEAL)
    _text(draw, (118, y + 242), "Aldım", _font(30, True), WHITE)
    _round_rect(draw, (300, y + 220, 530, y + 300), 20, RED)
    _text(draw, (348, y + 242), "Verdim", _font(30, True), WHITE)
    _round_rect(draw, (550, y + 220, W - 64, y + 300), 20, WHITE)
    _text(draw, (580, y + 242), "Sesle / fişle", _font(26, True), INK)

    y = 720
    metrics = [
        ("Kasadaki para", "₺4.250,00", TEAL_SOFT, TEAL),
        ("Alacakların", "₺1.650,00", AMBER, GOLD),
        ("Bu ay aldım", "₺4.890,00", (234, 242, 255), (53, 101, 168)),
        ("Bu ay verdim", "₺4.120,00", (255, 240, 239), RED),
    ]
    for i, (label, value, bg, accent) in enumerate(metrics):
        col = i % 2
        row = i // 2
        x0 = 36 + col * 516
        y0 = y + row * 200
        _round_rect(draw, (x0, y0, x0 + 492, y0 + 180), 28, bg, BORDER)
        _text(draw, (x0 + 28, y0 + 28), label, _font(24), MUTED)
        _text(draw, (x0 + 28, y0 + 72), value, _font(40, True), INK)
        _round_rect(draw, (x0 + 28, y0 + 128, x0 + 220, y0 + 160), 999, WHITE)
        _text(draw, (x0 + 44, y0 + 132), "Anlık özet", _font(20, True), accent)

    _nav(draw, "home")
    return img


def shot_ledger() -> Image.Image:
    img = Image.new("RGBA", (W, H), CANVAS + (255,))
    draw = _phone_chrome(img)
    _caption_banner(draw, "Para hareketleri", "Kasaya girdi · kasadan çıktı")
    y = 360
    _round_rect(draw, (36, y, 520, y + 180), 28, TEAL)
    _text(draw, (70, y + 48), "Aldım", _font(42, True), WHITE)
    _text(draw, (70, y + 110), "Kasaya girdi", _font(24), (255, 255, 255, 200))
    _round_rect(draw, (548, y, W - 36, y + 180), 28, RED)
    _text(draw, (590, y + 48), "Verdim", _font(42, True), WHITE)
    _text(draw, (590, y + 110), "Kasadan çıktı", _font(24), (255, 255, 255, 200))

    rows = [
        ("Günlük satış", "Aldım", "+₺1.850,00", TEAL),
        ("Toptancı ödeme", "Verdim", "−₺620,00", RED),
        ("Mehmet Kaya veresiye", "Veresiye", "₺450,00", GOLD),
        ("Nakit satış", "Aldım", "+₺940,00", TEAL),
    ]
    y = 580
    for title, kind, amount, color in rows:
        _round_rect(draw, (36, y, W - 36, y + 140), 24, CARD, BORDER)
        _text(draw, (64, y + 32), title, _font(30, True), INK)
        _text(draw, (64, y + 80), kind, _font(24), MUTED)
        bbox = draw.textbbox((0, 0), amount, font=_font(30, True))
        tw = bbox[2] - bbox[0]
        _text(draw, (W - 64 - tw, y + 48), amount, _font(30, True), color)
        y += 160

    _nav(draw, "ledger")
    return img


def shot_customers() -> Image.Image:
    img = Image.new("RGBA", (W, H), CANVAS + (255,))
    draw = _phone_chrome(img)
    _caption_banner(draw, "Veresiye defteri", "PDF ekstre + WhatsApp hatırlatma")
    y = 360
    _round_rect(draw, (36, y, W - 36, y + 220), 32, NAVY)
    _text(draw, (64, y + 40), "Açık alacak", _font(26, True), (158, 217, 203))
    _text(draw, (64, y + 90), "₺1.650,00", _font(56, True), WHITE)
    _text(draw, (64, y + 168), "2 borçlu müşteri", _font(26), WHITE)

    y = 620
    _round_rect(draw, (36, y, W - 36, y + 90), 22, TEAL)
    _text(draw, (W // 2 - 120, y + 28), "+ Müşteri ekle", _font(30, True), WHITE)

    people = [
        ("M", "Mehmet Kaya", "₺450,00 · 2 gün", True),
        ("G", "Güneş Sitesi", "₺1.200,00 · 5 gün", True),
        ("Z", "Zeynep Aksoy", "Bakiye yok", False),
    ]
    y = 740
    for letter, name, detail, owed in people:
        _round_rect(draw, (36, y, W - 36, y + 170), 28, CARD, BORDER)
        bg = (232, 163, 23) if owed else TEAL
        _round_rect(draw, (64, y + 40, 148, y + 124), 22, bg)
        _text(draw, (90, y + 62), letter, _font(40, True), WHITE if not owed else INK)
        _text(draw, (180, y + 42), name, _font(32, True), INK)
        _text(draw, (180, y + 96), detail, _font(24), GOLD if owed else MUTED)
        if owed:
            _round_rect(draw, (W - 280, y + 50, W - 64, y + 120), 18, AMBER)
            _text(draw, (W - 250, y + 68), "WhatsApp", _font(24, True), INK)
        y += 190

    _nav(draw, "customers")
    return img


def shot_intake() -> Image.Image:
    img = Image.new("RGBA", (W, H), CANVAS + (255,))
    draw = _phone_chrome(img)
    _caption_banner(draw, "Sesle / fişle kayıt", "Konuş veya fiş fotoğrafı çek")
    y = 360
    _text(draw, (48, y), "Ne kaydediyorsun?", _font(36, True), INK)
    y += 70
    for label, bg, fg, x0, x1 in (
        ("Aldım", TEAL, WHITE, 36, 340),
        ("Verdim", (255, 232, 230), RED, 360, 670),
        ("Veresiye", AMBER, INK, 690, W - 36),
    ):
        _round_rect(draw, (x0, y, x1, y + 90), 999, bg)
        tw = draw.textbbox((0, 0), label, font=_font(28, True))
        _text(draw, ((x0 + x1) // 2 - (tw[2] - tw[0]) // 2, y + 28), label, _font(28, True), fg)

    y += 130
    _round_rect(draw, (36, y, W - 36, y + 160), 24, WHITE, BORDER)
    _text(draw, (64, y + 28), "Sesle veya yazarak anlat", _font(24), MUTED)
    _text(draw, (64, y + 78), "Mehmet Kaya'ya 450 TL veresiye yaz", _font(28, True), INK)

    y += 190
    for label, value in (("Tutar (TL)", "450"), ("Açıklama", "Veresiye"), ("Müşteri", "Mehmet Kaya")):
        _round_rect(draw, (36, y, W - 36, y + 110), 22, WHITE, BORDER)
        _text(draw, (64, y + 18), label, _font(22), MUTED)
        _text(draw, (64, y + 56), value, _font(30, True), INK)
        y += 130

    _round_rect(draw, (36, y + 20, W - 36, y + 120), 24, TEAL)
    _text(draw, (W // 2 - 70, y + 48), "Kaydet", _font(34, True), WHITE)
    _nav(draw, "home")
    return img


def shot_welcome() -> Image.Image:
    img = Image.new("RGBA", (W, H), CANVAS + (255,))
    draw = _phone_chrome(img)
    _caption_banner(draw, "İlk açılışta hazır", "Onayla → hemen kayda başla")
    y = 360
    _round_rect(draw, (36, y, W - 36, y + 300), 36, NAVY)
    _text(draw, (64, y + 40), "Cebindeki kasa defteri", _font(24, True), (158, 217, 203))
    _text(draw, (64, y + 90), "Esnaf özeti", _font(48, True), WHITE)
    _text(draw, (64, y + 160), "Paranı doğru yönet, kârını gör.", _font(28), (215, 245, 238))
    _round_rect(draw, (64, y + 220, 280, y + 290), 20, TEAL)
    _text(draw, (118, y + 240), "Aldım", _font(30, True), WHITE)
    _round_rect(draw, (300, y + 220, 530, y + 290), 20, RED)
    _text(draw, (348, y + 240), "Verdim", _font(30, True), WHITE)

    y = 700
    _round_rect(draw, (36, y, W - 36, y + 360), 28, (255, 249, 237), BORDER)
    _text(draw, (64, y + 36), "Hemen başla", _font(36, True), INK)
    _text(draw, (64, y + 100), "Kasadaki parayı yaz veya ilk Aldım kaydını gir.", _font(26), MUTED)
    _text(draw, (64, y + 150), "İstersen örnek bakkal verisiyle önce gez.", _font(26), MUTED)
    buttons = [("Aldım", TEAL, WHITE), ("Veresiye yaz", AMBER, INK), ("Örnekle dene", (234, 242, 255), (53, 101, 168))]
    bx = 64
    for label, bg, fg in buttons:
        tw = draw.textbbox((0, 0), label, font=_font(26, True))
        width = (tw[2] - tw[0]) + 56
        _round_rect(draw, (bx, y + 230, bx + width, y + 310), 18, bg)
        _text(draw, (bx + 28, y + 252), label, _font(26, True), fg)
        bx += width + 20

    y = 1100
    _round_rect(draw, (36, y, W - 36, y + 220), 28, WHITE, BORDER)
    _text(draw, (64, y + 40), "Nakitçe'ye hoş geldin", _font(32, True), INK)
    _text(draw, (64, y + 100), "Aldım / Verdim ile hemen kayda başlayabilirsin.", _font(24), MUTED)
    _round_rect(draw, (64, y + 150, 320, y + 200), 16, TEAL)
    _text(draw, (120, y + 160), "Devam et", _font(26, True), WHITE)

    _nav(draw, "home")
    return img


SHOTS = [
    ("01_ozet_aldim_verdim.png", shot_home),
    ("02_para_hareketleri.png", shot_ledger),
    ("03_veresiye_defteri.png", shot_customers),
    ("04_sesle_fisle_kayit.png", shot_intake),
    ("05_ilk_acilis.png", shot_welcome),
]


def export_screenshots():
    STORE.mkdir(parents=True, exist_ok=True)
    written = []
    for name, builder in SHOTS:
        path = STORE / name
        builder().convert("RGB").save(path, "PNG", optimize=True)
        written.append(path)
    return written


def main():
    paths = export_screenshots()
    for path in paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
