import flet as ft

from free_quota import FREE_WHATSAPP_MONTHLY, whatsapp_used
from membership import premium_access
from views.common import AMBER_SOFT, INK, MINT, MUTED, TEAL, action_button, card, heading, money, section_label


def build(records, actions, workspace=None):
    workspace = workspace or {}
    premium = premium_access(workspace.get("_server_membership_status"))
    wa_used = whatsapp_used(workspace)
    rows = []
    open_balance = sum(c.get("balance", 0) for c in records["customers"] if c.get("balance", 0) > 0)
    debtor_count = sum(1 for c in records["customers"] if c.get("balance", 0) > 0)
    for customer in records["customers"]:
        has_debt = customer["balance"] > 0
        due = customer.get("due_date") or ""
        rows.append(
            card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=48,
                                    height=48,
                                    alignment=ft.Alignment.CENTER,
                                    border_radius=16,
                                    gradient=ft.LinearGradient(
                                        colors=["#E8A317", "#C7922A"] if has_debt else ["#0F9B82", "#0B1C2C"]
                                    ),
                                    content=ft.Text(
                                        customer["name"][:1].upper(),
                                        color=INK if has_debt else "white",
                                        weight=ft.FontWeight.BOLD,
                                        size=18,
                                    ),
                                ),
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                        ft.Text(customer["name"], color=INK, weight=ft.FontWeight.W_700, size=16),
                                        ft.Text(
                                            customer.get("phone") or "Telefon yok · WhatsApp için ekle",
                                            color=MUTED,
                                            size=12,
                                        ),
                                        ft.Text(
                                            f"Vade: {due}" if due else "Vade belirtilmedi",
                                            color="#C7922A" if has_debt else MUTED,
                                            size=11,
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=3,
                                    controls=[
                                        ft.Text(
                                            money(customer["balance"]),
                                            color="#C7922A" if has_debt else TEAL,
                                            weight=ft.FontWeight.BOLD,
                                            size=18,
                                        ),
                                        ft.Text("alacağım var" if has_debt else "temiz", color=MUTED, size=11),
                                    ],
                                ),
                            ]
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                ft.Button(
                                    content="Tahsil et",
                                    disabled=not has_debt,
                                    on_click=lambda e, c=customer: actions["collect"](c),
                                    bgcolor=MINT,
                                    color=TEAL,
                                ),
                                ft.Button(
                                    content="WhatsApp + PDF",
                                    disabled=not has_debt,
                                    on_click=lambda e, c=customer: actions["remind"](c),
                                    bgcolor="#25D366",
                                    color="white",
                                    tooltip="Paylaşım sayfasından WhatsApp seç; telefonsuz da çalışır",
                                ),
                                ft.TextButton(
                                    content="Sadece PDF",
                                    disabled=not has_debt,
                                    on_click=lambda e, c=customer: actions["statement_pdf"](c),
                                ),
                                ft.TextButton(
                                    content="Sil",
                                    on_click=lambda e, c=customer: actions["delete_customer"](c),
                                ),
                            ],
                        ),
                    ],
                ),
                bgcolor=AMBER_SOFT if has_debt else "white",
            )
        )

    hero = ft.Container(
        padding=18,
        border_radius=22,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#0B1C2C", "#0F4C45", "#0F9B82"],
        ),
        content=ft.Row(
            controls=[
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        ft.Text("Toplam açık hesap", color="#B7E8DC", size=12),
                        ft.Text(money(open_balance), color="white", weight=ft.FontWeight.BOLD, size=30),
                        ft.Text("Tek tuşla nazik WhatsApp ekstresi", color="#D7F5EE", size=12),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor="#FFFFFF22",
                    content=ft.Text(f"{debtor_count} borçlu", color="white", weight=ft.FontWeight.W_700),
                ),
            ]
        ),
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            heading(
                "Veresiye defteri",
                "Sınırsız WhatsApp ekstresi."
                if premium
                else f"WhatsApp bu ay {min(wa_used, FREE_WHATSAPP_MONTHLY)}/{FREE_WHATSAPP_MONTHLY} ücretsiz. Veresiye yazmak sınırlı değil.",
            ),
            hero,
            action_button("+ Müşteri ekle", actions["add"], primary=True),
            section_label(f"Müşterilerim · {len(records['customers'])}"),
            *(
                rows
                or [
                    card(
                        ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("Henüz müşteri yok.", color=MUTED, size=13),
                                ft.Text("Veresiye yazınca müşteri otomatik oluşur; istersen önce kart ekleyebilirsin.", color=MUTED, size=12),
                                ft.Row(
                                    wrap=True,
                                    spacing=8,
                                    controls=[
                                        ft.Button(content="Veresiye yaz", on_click=actions["debt"], bgcolor=TEAL, color="white"),
                                        ft.Button(content="+ Müşteri ekle", on_click=actions["add"]),
                                    ],
                                ),
                            ],
                        )
                    )
                ]
            ),
        ],
    )
