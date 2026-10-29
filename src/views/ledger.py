import flet as ft

from views.common import INK, MUTED, RED, TEAL, action_button, big_choice, card, heading, money, section_label


def build(records, actions, evidence):
    transactions = sorted(records["transactions"], key=lambda t: t.get("date", ""), reverse=True)
    rows = []
    for item in transactions:
        incoming = item["type"] == "income"
        is_debt = item["type"] == "debt"
        rows.append(
            card(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=10,
                            height=48,
                            border_radius=6,
                            bgcolor=TEAL if incoming else ("#D79A28" if is_debt else RED),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(item["title"], color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    f"{item.get('date', '')} · {'Aldım' if incoming else ('Veresiye' if is_debt else 'Verdim')}",
                                    color=MUTED,
                                    size=12,
                                ),
                            ],
                        ),
                        ft.Text(
                            ("+ " if incoming else ("Veresiye · " if is_debt else "− ")) + money(item["amount"]),
                            color=TEAL if incoming else ("#A66A08" if is_debt else RED),
                            weight=ft.FontWeight.BOLD,
                        ),
                        *(
                            [
                                ft.TextButton(
                                    content=f"Ekler ({len(evidence[str(item['id'])])})",
                                    on_click=lambda e, transaction_id=item["id"]: actions["evidence"](transaction_id),
                                )
                            ]
                            if str(item["id"]) in evidence
                            else []
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=MUTED,
                            tooltip="Kaydı sil (yanlış girdiysen)",
                            on_click=lambda e, t=item: actions["delete_transaction"](t),
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
            heading("Para hareketleri", "Defter tutar gibi: Aldım / Verdim."),
            ft.Row(
                spacing=10,
                controls=[
                    big_choice("Aldım", "Kasaya girdi", actions["income"], tone="teal"),
                    big_choice("Verdim", "Kasadan çıktı", actions["expense"], tone="red"),
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=8,
                controls=[
                    action_button("Sesle / fişle kayıt", actions["intake"], primary=True),
                    action_button("Veresiye", actions["debt"]),
                ],
            ),
            section_label(f"Tüm hareketler · {len(transactions)} kayıt"),
            *(rows or [card(ft.Text("Henüz hareket yok. İlk kaydı Aldım veya Verdim ile ekle.", color=MUTED))]),
        ],
    )
