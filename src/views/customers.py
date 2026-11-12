import flet as ft

from free_quota import FREE_WHATSAPP_MONTHLY, whatsapp_used
from membership import premium_access
from views.common import (
    AMBER_SOFT,
    INK,
    MINT,
    MUTED,
    TEAL,
    WHITE,
    action_button,
    avatar,
    card,
    empty_state,
    heading,
    money,
    section_label,
)


def build(records, actions, workspace=None):
    workspace = workspace or {}
    premium = premium_access(workspace.get("_server_membership_status"))
    wa_used = whatsapp_used(workspace)
    rows = []
    open_balance = sum(c.get("balance", 0) for c in records["customers"] if c.get("balance", 0) > 0)
    debtor_count = sum(1 for c in records["customers"] if c.get("balance", 0) > 0)
    ordered = sorted(
        records["customers"],
        key=lambda c: (0 if c.get("balance", 0) > 0 else 1, -(c.get("balance", 0) or 0), c.get("name", "")),
    )
    for customer in ordered:
        has_debt = customer["balance"] > 0
        due = customer.get("due_date") or ""
        rows.append(
            card(
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                avatar(customer["name"][:1], owed=has_debt),
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                        ft.Text(customer["name"], color=INK, weight=ft.FontWeight.W_700, size=16),
                                        ft.Text(
                                            customer.get("phone") or "Telefon yok",
                                            color=MUTED,
                                            size=12,
                                        ),
                                        ft.Text(
                                            f"Vade {due}" if due else "Vade belirtilmedi",
                                            color="#C7922A" if has_debt else MUTED,
                                            size=11,
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            money(customer["balance"]),
                                            color="#C7922A" if has_debt else TEAL,
                                            weight=ft.FontWeight.BOLD,
                                            size=18,
                                        ),
                                        ft.Text("alacak" if has_debt else "temiz", color=MUTED, size=11),
                                    ],
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    height=46,
                                    border_radius=14,
                                    bgcolor=MINT if has_debt else "#F2F5F4",
                                    alignment=ft.Alignment.CENTER,
                                    opacity=1 if has_debt else 0.55,
                                    on_click=(lambda e, c=customer: actions["collect"](c)) if has_debt else None,
                                    ink=has_debt,
                                    content=ft.Text("Tahsil et", color=TEAL, weight=ft.FontWeight.W_700),
                                ),
                                ft.Container(
                                    expand=True,
                                    height=46,
                                    border_radius=14,
                                    bgcolor="#25D366" if has_debt else "#F2F5F4",
                                    alignment=ft.Alignment.CENTER,
                                    opacity=1 if has_debt else 0.55,
                                    on_click=(lambda e, c=customer: actions["remind"](c)) if has_debt else None,
                                    ink=has_debt,
                                    content=ft.Text("WhatsApp", color=WHITE if has_debt else MUTED, weight=ft.FontWeight.W_700),
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.TextButton(
                                    content="PDF ekstre",
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
                bgcolor=AMBER_SOFT if has_debt else WHITE,
                padding=16,
                radius=20,
            )
        )

    hero = ft.Container(
        padding=20,
        border_radius=26,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#0B1C2C", "#0F4C45", "#0F9B82"],
        ),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        ft.Text("Açık alacak", color="#B7E8DC", size=12),
                        ft.Text(money(open_balance), color=WHITE, weight=ft.FontWeight.BOLD, size=32),
                        ft.Text("WhatsApp ile nazik ekstre", color="#D7F5EE", size=12),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor="#FFFFFF22",
                    content=ft.Text(f"{debtor_count} borçlu", color=WHITE, weight=ft.FontWeight.W_700),
                ),
            ],
        ),
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            heading(
                "Veresiye",
                "Sınırsız WhatsApp."
                if premium
                else f"WhatsApp {min(wa_used, FREE_WHATSAPP_MONTHLY)}/{FREE_WHATSAPP_MONTHLY} · veresiye sınırsız",
            ),
            hero,
            ft.Row(
                spacing=8,
                controls=[
                    action_button("Veresiye yaz", actions["debt"], primary=True),
                    action_button("+ Müşteri", actions["add"]),
                ],
            ),
            section_label(f"Müşteriler · {len(records['customers'])}"),
            *(
                rows
                or [
                    empty_state(
                        "Henüz müşteri yok",
                        "Veresiye yazınca kart otomatik oluşur.",
                        button_label="Veresiye yaz",
                        on_click=actions["debt"],
                        secondary_label="+ Müşteri ekle",
                        on_secondary=actions["add"],
                    )
                ]
            ),
        ],
    )
