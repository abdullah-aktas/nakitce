import flet as ft


INK = "#0E2433"


def camera_supported(page) -> bool:
    """flet-camera yalnızca Android / iOS / Web'de; masaüstünde oluşturmak diyalogu kırar."""
    if getattr(page, "web", False):
        return True
    platform = getattr(page, "platform", None)
    return platform in {
        ft.PagePlatform.ANDROID,
        ft.PagePlatform.ANDROID_TV,
        ft.PagePlatform.IOS,
    }
MUTED = "#5B7382"
TEAL = "#0F9B82"
TEAL_DEEP = "#0B7A67"
MINT = "#E4F8F2"
CANVAS = "#EEF3F2"
WHITE = "#FFFFFF"
AMBER = "#E8A317"
AMBER_SOFT = "#FFF6E0"
RED = "#D64545"
RED_SOFT = "#FFE8E6"
BLUE = "#2F6FED"
BLUE_SOFT = "#E8F0FF"
GOLD = "#C7922A"


def page_gradient():
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#F7FBFA", "#E8F4F1", "#F3F0EA"],
    )


def hero_gradient():
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#0B1C2C", "#0F4C45", "#168F79"],
    )


def card(content, *, bgcolor=WHITE, col=None, padding=16, border=None):
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=padding,
        border_radius=20,
        col=col,
        border=border or ft.Border.all(1, "#E4ECE9"),
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=0,
            color="#14000000",
            offset=ft.Offset(0, 6),
        ),
    )


def heading(title, subtitle=None):
    controls = [ft.Text(title, size=26, weight=ft.FontWeight.BOLD, color=INK)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=MUTED))
    return ft.Column(controls=controls, spacing=4, tight=True)


def section_label(label, trailing=None):
    parts = [ft.Text(label, size=16, weight=ft.FontWeight.W_700, color=INK)]
    if trailing:
        parts.append(trailing)
    return ft.Row(controls=parts, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def money(value):
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def action_button(label, on_click, *, primary=False, color=None, bgcolor=None):
    return ft.Button(
        content=ft.Text(label, weight=ft.FontWeight.W_600),
        on_click=on_click,
        bgcolor=bgcolor if bgcolor is not None else (TEAL if primary else WHITE),
        color=color if color is not None else (WHITE if primary else INK),
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=16),
        ),
    )


def big_choice(label, subtitle, on_click, *, tone="teal"):
    tones = {
        "teal": (TEAL, MINT, WHITE),
        "red": (RED, RED_SOFT, WHITE),
        "amber": (GOLD, AMBER_SOFT, INK),
        "ink": (INK, "#E8EEF2", WHITE),
    }
    bg, soft, fg = tones.get(tone, tones["teal"])
    return ft.Container(
        expand=True,
        padding=16,
        border_radius=22,
        bgcolor=bg,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(blur_radius=16, color="#22000000", offset=ft.Offset(0, 8)),
        content=ft.Column(
            spacing=4,
            tight=True,
            controls=[
                ft.Text(label, size=20, weight=ft.FontWeight.BOLD, color=fg),
                ft.Text(subtitle, size=12, color=MUTED if tone == "amber" else "#FFFFFFCC"),
            ],
        ),
    )


def chip(label, *, selected=False, on_click=None, tone="teal"):
    active = TEAL if tone == "teal" else (RED if tone == "red" else GOLD)
    # Sarı/amber seçilince beyaz okunmaz → siyah; yeşil/kırmızıda beyaz kalır.
    selected_fg = INK if tone == "amber" else WHITE
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        border_radius=999,
        bgcolor=active if selected else WHITE,
        border=ft.Border.all(1, active if selected else "#D7E3DF"),
        on_click=on_click,
        ink=True,
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.W_600,
            color=selected_fg if selected else INK,
        ),
    )


def metric_tile(label, value, caption, *, bgcolor=MINT, accent=TEAL, col=None):
    return card(
        ft.Column(
            spacing=8,
            controls=[
                ft.Text(label, size=12, color=MUTED, weight=ft.FontWeight.W_500),
                ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=INK),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    border_radius=999,
                    bgcolor=WHITE,
                    content=ft.Text(caption, size=11, color=accent, weight=ft.FontWeight.W_600),
                ),
            ],
        ),
        bgcolor=bgcolor,
        col=col,
    )


def alert_card(title, subtitle, *, tone="amber", on_click=None):
    palette = {
        "red": (RED_SOFT, RED),
        "amber": (AMBER_SOFT, GOLD),
        "teal": (MINT, TEAL),
    }
    bg, accent = palette.get(tone, palette["amber"])
    return card(
        ft.Row(
            spacing=12,
            controls=[
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=14,
                    bgcolor=WHITE,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=accent, size=22),
                ),
                ft.Column(
                    expand=True,
                    spacing=3,
                    controls=[
                        ft.Text(title, color=INK, weight=ft.FontWeight.W_700, size=14),
                        ft.Text(subtitle, color=MUTED, size=12),
                    ],
                ),
            ],
        ),
        bgcolor=bg,
    )
