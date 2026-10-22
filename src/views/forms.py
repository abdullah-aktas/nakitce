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
    "pos": [("bank", "Banka / POS adı", "Banka POS"), ("gross", "Brüt satış (TL)", ""), ("rate", "Kesinti oranı (%)", "2.49"), ("days", "Ödeme kaç gün sonra?", "3")],
    "quote": [("customer", "Müşteri adı", ""), ("title", "Yapılacak iş", ""), ("materials", "Malzeme tutarı (TL)", "0"), ("labor", "İşçilik tutarı (TL)", "0")],
    "sync": [("project_url", "Supabase Project URL", "https://your-project.supabase.co"), ("anon_key", "Supabase anon / publishable key", ""), ("email", "Hesap e-postası", ""), ("password", "Hesap parolası", "")],
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
    "pos": "POS ödemesi ekle",
    "quote": "Hızlı teklif oluştur",
    "sync": "Supabase bulut eşitlemesi",
}


def show_form(page, kind, submit, subject=None):
    controls = {}
    field_controls = []
    for key, label, default in FORM_FIELDS[kind]:
        if kind == "sync" and subject:
            default = subject.get(key, default)
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
        values = {key: control.value or "" for key, control in controls.items()}
        if await submit(kind, values, subject):
            page.pop_dialog()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(FORM_TITLES[kind], color=INK, weight=ft.FontWeight.BOLD),
        content=ft.Column(controls=([ft.Text("Kendi Supabase projenin SQL Editor bölümünde supabase_schema.sql dosyasını çalıştırıp Auth hesabı oluştur. Project URL, public anon/publishable key ve hesap bilgilerini gir. Kayıtlar senin projenle eşitlenir; Supabase plan/kullanım ücretini doğrudan Supabase'e sen ödersin. Bu ücret Nakitçe Premium'dan ayrıdır; Nakitçe parolanı saklamaz.", color=INK, size=12)] if kind == "sync" else []) + ([ft.Text(f"Müşteri: {subject['name']}", color=INK)] if kind == "collect" and subject else []) + ([ft.Text(f"Ürün: {subject['name']} · {subject['price']:.2f} TL / adet", color=INK)] if kind == "sale" and subject else []) + field_controls, tight=True, spacing=10, width=340, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
            ft.Button(content="Kaydet", on_click=save, bgcolor=TEAL, color="white"),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)
