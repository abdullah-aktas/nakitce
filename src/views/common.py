import flet as ft


INK = "#0E2433"
MUTED = "#5B7382"
TEAL = "#0F9B82"
TEAL_DEEP = "#0B7A67"
MINT = "#E4F8F2"
CANVAS = "#F3F6F5"
WHITE = "#FFFFFF"
AMBER = "#E8A317"
AMBER_SOFT = "#FFF6E0"
RED = "#D64545"
RED_SOFT = "#FFE8E6"
BLUE = "#2F6FED"
BLUE_SOFT = "#E8F0FF"
GOLD = "#C7922A"
LINE = "#E2EBE8"
SOFT_SHADOW = ft.BoxShadow(blur_radius=14, spread_radius=0, color="#12000000", offset=ft.Offset(0, 5))


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


def page_gradient():
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#F8FBFA", "#EEF6F3", "#F4F1EA"],
    )


def hero_gradient():
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#0B1C2C", "#0F4C45", "#168F79"],
    )


def card(content, *, bgcolor=WHITE, col=None, padding=16, border=None, radius=22):
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=padding,
        border_radius=radius,
        col=col,
        border=border or ft.Border.all(1, LINE),
        shadow=SOFT_SHADOW,
    )


def soft_panel(content, *, bgcolor=WHITE, padding=16, radius=22):
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=padding,
        border_radius=radius,
        border=ft.Border.all(1, LINE),
    )


def heading(title, subtitle=None):
    controls = [ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=INK)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=MUTED))
    return ft.Column(controls=controls, spacing=4, tight=True)


def section_label(label, trailing=None):
    parts = [ft.Text(label, size=15, weight=ft.FontWeight.W_700, color=INK)]
    if trailing:
        parts.append(trailing)
    return ft.Row(controls=parts, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def money(value):
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def action_button(label, on_click, *, primary=False, color=None, bgcolor=None):
    return ft.Button(
        content=ft.Text(label, weight=ft.FontWeight.W_600, size=14),
        on_click=on_click,
        bgcolor=bgcolor if bgcolor is not None else (TEAL if primary else WHITE),
        color=color if color is not None else (WHITE if primary else INK),
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=16),
        ),
    )


def primary_cta(label, on_click, *, tone="teal", expand=True):
    tones = {
        "teal": (TEAL, WHITE),
        "red": (RED, WHITE),
        "amber": (AMBER, INK),
        "mint": (MINT, TEAL_DEEP),
        "ink": (INK, WHITE),
        "wa": ("#25D366", WHITE),
    }
    bg, fg = tones.get(tone, tones["teal"])
    return ft.Container(
        expand=expand,
        height=56,
        border_radius=18,
        bgcolor=bg,
        alignment=ft.Alignment.CENTER,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(blur_radius=12, color="#22000000", offset=ft.Offset(0, 5)),
        content=ft.Text(label, size=16, weight=ft.FontWeight.BOLD, color=fg),
    )


def big_choice(label, subtitle, on_click, *, tone="teal"):
    tones = {
        "teal": (TEAL, WHITE, "#FFFFFFCC"),
        "red": (RED, WHITE, "#FFFFFFCC"),
        "amber": (AMBER, INK, "#5B7382"),
        "ink": (INK, WHITE, "#FFFFFFCC"),
    }
    bg, fg, sub = tones.get(tone, tones["teal"])
    return ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(horizontal=14, vertical=18),
        border_radius=20,
        bgcolor=bg,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(blur_radius=14, color="#22000000", offset=ft.Offset(0, 6)),
        content=ft.Column(
            spacing=4,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(label, size=22, weight=ft.FontWeight.BOLD, color=fg),
                ft.Text(subtitle, size=12, color=sub),
            ],
        ),
    )


def chip(label, *, selected=False, on_click=None, tone="teal"):
    active = TEAL if tone == "teal" else (RED if tone == "red" else GOLD)
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
            spacing=6,
            controls=[
                ft.Text(label, size=12, color=MUTED, weight=ft.FontWeight.W_500),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=INK),
                ft.Text(caption, size=11, color=accent, weight=ft.FontWeight.W_600),
            ],
        ),
        bgcolor=bgcolor,
        col=col,
        padding=14,
        radius=18,
    )


def empty_state(title, subtitle, *, button_label=None, on_click=None, secondary_label=None, on_secondary=None):
    buttons = []
    if button_label and on_click:
        buttons.append(ft.Button(content=button_label, on_click=on_click, bgcolor=TEAL, color=WHITE))
    if secondary_label and on_secondary:
        buttons.append(ft.Button(content=secondary_label, on_click=on_secondary, bgcolor=AMBER_SOFT, color=INK))
    return card(
        ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Text(title, color=INK, weight=ft.FontWeight.W_700, size=15),
                ft.Text(subtitle, color=MUTED, size=13),
                *([ft.Row(wrap=True, spacing=8, controls=buttons)] if buttons else []),
            ],
        ),
        bgcolor="#FAFCFB",
    )


def alert_card(title, subtitle, *, tone="amber", on_click=None):
    palette = {
        "red": (RED_SOFT, RED, ft.Icons.WARNING_AMBER_ROUNDED),
        "amber": (AMBER_SOFT, GOLD, ft.Icons.NOTIFICATIONS_ACTIVE),
        "teal": (MINT, TEAL, ft.Icons.CHECK_CIRCLE_OUTLINE),
    }
    bg, accent, icon = palette.get(tone, palette["amber"])
    return card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=14,
                    bgcolor=WHITE,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(icon, color=accent, size=22),
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
        padding=14,
        radius=18,
    )


def avatar(letter, *, owed=False):
    return ft.Container(
        width=48,
        height=48,
        alignment=ft.Alignment.CENTER,
        border_radius=16,
        gradient=ft.LinearGradient(
            colors=["#E8A317", "#C7922A"] if owed else ["#0F9B82", "#0B1C2C"],
        ),
        content=ft.Text(
            (letter or "?").upper()[:1],
            color=INK if owed else WHITE,
            weight=ft.FontWeight.BOLD,
            size=18,
        ),
    )
