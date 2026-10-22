import flet as ft

from views.common import INK, MUTED, TEAL, action_button, card, heading, money, section_label


def build(records, actions):
    rows = []
    for customer in records["customers"]:
        rows.append(
            card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(width=42, height=42, alignment=ft.Alignment.CENTER, border_radius=14, bgcolor="#E8F7F2", content=ft.Text(customer["name"][:1].upper(), color=TEAL, weight=ft.FontWeight.BOLD)),
                                ft.Column(expand=True, spacing=3, controls=[ft.Text(customer["name"], color=INK, weight=ft.FontWeight.W_600), ft.Text(customer.get("phone") or "Telefon eklenmemiş", color=MUTED, size=12)]),
                                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.END, spacing=3, controls=[ft.Text(money(customer["balance"]), color="#A66A08" if customer["balance"] > 0 else TEAL, weight=ft.FontWeight.BOLD), ft.Text("alacağı var" if customer["balance"] > 0 else "bakiye", color=MUTED, size=11)]),
                            ]
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                ft.Button(content="Tahsilat ekle", disabled=customer["balance"] <= 0, on_click=lambda e, c=customer: actions["collect"](c), bgcolor="#E8F7F2", color=TEAL),
                                ft.Button(content="WhatsApp hatırlat", disabled=not customer.get("phone") or customer["balance"] <= 0, on_click=lambda e, c=customer: actions["remind"](c), bgcolor="#F2F5F4", color=INK),
                            ],
                        ),
                    ],
                )
            )
        )
    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            heading("Veresiye defteri", "Müşterinin açık hesabı, sade ve anlaşılır."),
            action_button("+ Müşteri ekle", actions["add"], primary=True),
            section_label(f"Müşterilerim · {len(records['customers'])}"),
            *(rows or [card(ft.Text("Henüz müşteri eklenmemiş.", color=MUTED))]),
        ],
    )
