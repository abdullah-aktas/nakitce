import flet as ft

from views.common import INK, TEAL


FORM_FIELDS = {
    "income": [("title", "Ne için para geldi?", "Günlük satış"), ("amount", "Tutar (TL)", "")],
    "expense": [("title", "Ne için para çıktı?", "Mal alımı"), ("amount", "Tutar (TL)", "")],
    "debt": [("name", "Müşteri adı", ""), ("amount", "Veresiye tutarı (TL)", "")],
    "collect": [("amount", "Tahsil edilen tutar (TL)", "")],
    "customer": [("name", "Müşteri adı", ""), ("phone", "Telefon (ülke koduyla)", "")],
    "product": [("name", "Ürün veya hizmet adı", ""), ("barcode", "Barkod (isteğe bağlı)", ""), ("qty", "Mevcut stok", "0"), ("min_qty", "Az stok uyarısı", "0"), ("price", "Satış fiyatı (TL)", "")],
    "sale": [("qty", "Satılan adet", "1")],
    "lookup": [("barcode", "Barkod numarası", "")],
    "opening": [("amount", "Şu an kasadaki nakit (TL)", "0")],
    "pos": [("bank", "Banka / POS adı", "Banka POS"), ("gross", "Brüt satış (TL)", ""), ("rate", "Kesinti oranı (%)", "2.49"), ("days", "Ödeme kaç gün sonra?", "3")],
    "quote": [("customer", "Müşteri adı", ""), ("title", "Yapılacak iş", ""), ("materials", "Malzeme tutarı (TL)", "0"), ("labor", "İşçilik tutarı (TL)", "0")],
}

FORM_TITLES = {
    "income": "Gelen para ekle",
    "expense": "Giden para ekle",
    "debt": "Veresiye ekle",
    "collect": "Tahsilat ekle",
    "customer": "Müşteri ekle",
    "product": "Ürün / hizmet ekle",
    "sale": "Hızlı satış",
    "lookup": "Barkodla ürün bul",
    "opening": "Kasadaki parayı ayarla",
    "pos": "POS ödemesi ekle",
    "quote": "Hızlı teklif oluştur",
}


def show_form(page, kind, submit, subject=None):
    from views.common import RED

    controls = {}
    field_controls = []
    notice = ft.Text("", color=RED, size=12, visible=False)
    for key, label, default in FORM_FIELDS[kind]:
        field = ft.TextField(
            label=label,
            value=default,
            password=key == "password",
            can_reveal_password=key == "password",
            keyboard_type=ft.KeyboardType.NUMBER if key in {"amount", "qty", "min_qty", "price", "gross", "rate", "days", "materials", "labor"} else (ft.KeyboardType.EMAIL if key == "email" else ft.KeyboardType.TEXT),
            autofocus=not controls,
        )
        controls[key] = field
        field_controls.append(field)

    async def save():
        notice.visible = False
        notice.value = ""
        values = {key: control.value or "" for key, control in controls.items()}
        result = await submit(kind, values, subject)
        if result is True:
            page.pop_dialog()
            return
        notice.value = result if isinstance(result, str) else "Bilgileri kontrol edip tekrar dene."
        notice.visible = True
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(FORM_TITLES[kind], color=INK, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            controls=(
                ([ft.Text(f"Müşteri: {subject['name']}", color=INK)] if kind == "collect" and subject else [])
                + ([ft.Text(f"Ürün: {subject['name']} · {subject['price']:.2f} TL / adet", color=INK)] if kind == "sale" and subject else [])
                + field_controls
                + [notice]
            ),
            tight=True,
            spacing=10,
            width=340,
            scroll=ft.ScrollMode.AUTO,
        ),
        actions=[
            ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
            ft.Button(content="Kaydet", on_click=save, bgcolor=TEAL, color="white"),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)
