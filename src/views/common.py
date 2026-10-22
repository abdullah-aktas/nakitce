import flet as ft


INK = "#132B3A"
MUTED = "#647985"
TEAL = "#168F79"
MINT = "#E8F7F2"
CANVAS = "#F4F7F6"
WHITE = "#FFFFFF"
AMBER = "#F6B94A"
RED = "#C94F4F"


def card(content, *, bgcolor=WHITE, col=None):
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        padding=16,
        border_radius=16,
        col=col,
    )


def heading(title, subtitle=None):
    controls = [ft.Text(title, size=23, weight=ft.FontWeight.BOLD, color=INK)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=MUTED))
    return ft.Column(controls=controls, spacing=4, tight=True)


def section_label(label, trailing=None):
    parts = [ft.Text(label, size=16, weight=ft.FontWeight.W_600, color=INK)]
    if trailing:
        parts.append(trailing)
    return ft.Row(controls=parts, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)


def money(value):
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def action_button(label, on_click, *, primary=False):
    return ft.Button(
        content=ft.Text(label, weight=ft.FontWeight.W_600),
        on_click=on_click,
        bgcolor=TEAL if primary else WHITE,
        color=WHITE if primary else INK,
        style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=16, vertical=12)),
    )
