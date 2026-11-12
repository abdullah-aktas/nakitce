import flet as ft

from views.common import (
    INK,
    MUTED,
    RED,
    TEAL,
    action_button,
    big_choice,
    card,
    empty_state,
    heading,
    money,
    section_label,
)


def build(records, actions, evidence):
    transactions = sorted(records["transactions"], key=lambda t: t.get("date", ""), reverse=True)
    rows = []
    for item in transactions:
        incoming = item["type"] == "income"
        is_debt = item["type"] == "debt"
        tone = TEAL if incoming else ("#D79A28" if is_debt else RED)
        kind = "Aldım" if incoming else ("Veresiye" if is_debt else "Verdim")
        rows.append(
            card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=8, height=44, border_radius=8, bgcolor=tone),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(item["title"], color=INK, weight=ft.FontWeight.W_600, size=15),
                                ft.Text(f"{item.get('date', '')} · {kind}", color=MUTED, size=12),
                            ],
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=2,
                            controls=[
                                ft.Text(
                                    ("+" if incoming else ("· " if is_debt else "−")) + money(item["amount"]),
                                    color=tone,
                                    weight=ft.FontWeight.BOLD,
                                    size=15,
                                ),
                                *(
                                    [
                                        ft.TextButton(
                                            content=f"Ek ({len(evidence[str(item['id'])])})",
                                            on_click=lambda e, transaction_id=item["id"]: actions["evidence"](transaction_id),
                                        )
                                    ]
                                    if str(item["id"]) in evidence
                                    else []
                                ),
                            ],
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=MUTED,
                            icon_size=20,
                            tooltip="Kaydı sil",
                            on_click=lambda e, t=item: actions["delete_transaction"](t),
                        ),
                    ],
                ),
                padding=14,
                radius=18,
            )
        )
    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            heading("Hareketler", "Kasaya giren ve çıkan para."),
            ft.Row(
                spacing=10,
                controls=[
                    big_choice("Aldım", "Kasaya girdi", actions["income"], tone="teal"),
                    big_choice("Verdim", "Kasadan çıktı", actions["expense"], tone="red"),
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    action_button("Sesle / fişle", actions["intake"], primary=True),
                    action_button("Veresiye", actions["debt"], bgcolor="#FFF1D8"),
                ],
            ),
            section_label(f"Kayıtlar · {len(transactions)}"),
            *(
                rows
                or [
                    empty_state(
                        "Henüz hareket yok",
                        "İlk kaydı Aldım veya Verdim ile ekle.",
                        button_label="Aldım",
                        on_click=actions["income"],
                        secondary_label="Verdim",
                        on_secondary=actions["expense"],
                    )
                ]
            ),
        ],
    )
