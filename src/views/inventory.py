import flet as ft

from views.common import INK, MUTED, TEAL, action_button, card, empty_state, heading, money, section_label


def build(records, actions):
    rows = []
    for product in records["products"]:
        low = bool(product["min_qty"] and product["qty"] <= product["min_qty"])
        rows.append(
            card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            alignment=ft.Alignment.CENTER,
                            border_radius=15,
                            bgcolor="#FFF5E2" if low else "#E8F7F2",
                            content=ft.Icon(
                                ft.Icons.WARNING_AMBER_ROUNDED if low else ft.Icons.INVENTORY_2_OUTLINED,
                                color="#A66A08" if low else TEAL,
                                size=22,
                            ),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(product["name"], color=INK, weight=ft.FontWeight.W_700, size=15),
                                ft.Text(
                                    f"Stok {product['qty']} · {money(product['price'])}",
                                    color=MUTED,
                                    size=12,
                                ),
                                ft.Text(
                                    f"Barkod {product['barcode']}" if product.get("barcode") else "Hizmet kalemi",
                                    color=MUTED,
                                    size=11,
                                ),
                            ],
                        ),
                        ft.Button(
                            content="Sat",
                            on_click=lambda e, p=product: actions["sell"](p),
                            bgcolor=TEAL,
                            color="white",
                            style=ft.ButtonStyle(
                                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=MUTED,
                            icon_size=20,
                            tooltip="Kalemi sil",
                            on_click=lambda e, p=product: actions["delete_product"](p),
                        ),
                    ],
                ),
                bgcolor="#FFF9F7" if low else "#FFFFFF",
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
            heading("Stok", "Barkodu oku, satışa geç."),
            ft.Row(
                spacing=8,
                controls=[
                    action_button("+ Ürün / hizmet", actions["product_add"], primary=True),
                    action_button("Barkod tara", actions["lookup"]),
                ],
            ),
            section_label(f"Kalemler · {len(records['products'])}"),
            *(
                rows
                or [
                    empty_state(
                        "Henüz ürün yok",
                        "Ürün veya hizmet ekle; barkodla satışa geç.",
                        button_label="+ Ürün / hizmet ekle",
                        on_click=actions["product_add"],
                    )
                ]
            ),
            card(
                ft.Text(
                    "Kamerayı etikete tut (EAN-13, Code128, QR). Okununca satış açılır.",
                    size=12,
                    color=MUTED,
                ),
                padding=14,
                radius=16,
                bgcolor="#FAFCFB",
            ),
        ],
    )
