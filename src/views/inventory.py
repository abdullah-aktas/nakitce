import flet as ft

from views.common import INK, MUTED, RED, TEAL, action_button, card, heading, money, section_label


def build(records, actions):
    rows = []
    for product in records["products"]:
        low = bool(product["min_qty"] and product["qty"] <= product["min_qty"])
        rows.append(
            card(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            alignment=ft.Alignment.CENTER,
                            border_radius=14,
                            bgcolor="#FFF5E2" if low else "#E8F7F2",
                            content=ft.Text(
                                "!" if low else "□",
                                color="#A66A08" if low else TEAL,
                                weight=ft.FontWeight.BOLD,
                                size=18,
                            ),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                ft.Text(product["name"], color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(f"Stok: {product['qty']} · {money(product['price'])}", color=MUTED, size=12),
                                ft.Text(
                                    f"Barkod: {product['barcode']}" if product.get("barcode") else "Hizmet kalemi",
                                    color=MUTED,
                                    size=11,
                                ),
                            ],
                        ),
                        ft.Button(
                            content="Satış",
                            on_click=lambda e, p=product: actions["sell"](p),
                            bgcolor=TEAL,
                            color="white",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=MUTED,
                            tooltip="Kalemi sil",
                            on_click=lambda e, p=product: actions["delete_product"](p),
                        ),
                    ]
                ),
                bgcolor="#FFF9F7" if low else "#FFFFFF",
            )
        )
    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            heading("Ürünler ve stok", "Barkodu kameraya göster, satışa geç."),
            ft.Row(
                wrap=True,
                spacing=8,
                controls=[
                    action_button("+ Ürün / hizmet", actions["product_add"], primary=True),
                    action_button("Kamerayla barkod tara", actions["lookup"]),
                ],
            ),
            section_label(f"Kayıtlı kalemler · {len(records['products'])}"),
            *(rows or [card(ft.Text("Henüz ürün eklenmemiş.", color=MUTED))]),
            card(
                ft.Text(
                    "Barkod tarama: kamerayı aç, etiketi kadraja al (EAN-13, Code128, QR). "
                    "Okununca satış ekranı açılır. Masaüstünde kamera yoksa numarayı elle yazabilirsin.",
                    size=12,
                    color=MUTED,
                )
            ),
        ],
    )
