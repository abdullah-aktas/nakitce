import flet as ft

from views.common import INK, MUTED, TEAL

SECTORS = [
    "Bakkal / market",
    "Berber / kuaför",
    "Marangoz / mobilya",
    "Tesisat / teknik servis",
    "Butik / perakende",
    "Yeme içme",
    "Serbest meslek",
    "Diğer",
]
LEGAL_FORMS = ["Şahıs işletmesi", "Adi ortaklık", "Limited şirket", "Anonim şirket", "Esnaf işletmesi", "Diğer"]
SECTOR_CONFIG = {
    "Bakkal / market": {
        "title": "Dükkanın bugün",
        "summary": "Hızlı satış, raf stoğu ve POS takibini öne aldık.",
        "focus": "Hızlı satış · Stok · POS",
        "actions": ("sale", "income", "expense", "debt"),
    },
    "Berber / kuaför": {
        "title": "Dükkanın bugün",
        "summary": "Müşteri bakiyesi, günlük tahsilat ve ekipman bakımını öne aldık.",
        "focus": "Gelen para · Müşteriler · Bakım hatırlatması",
        "actions": ("income", "debt", "expense", "sale"),
    },
    "Marangoz / mobilya": {
        "title": "Atölyen bugün",
        "summary": "Malzeme gideri, müşteri işi ve teklif takibini öne aldık.",
        "focus": "Gider · Teklif · Malzeme stoğu",
        "actions": ("expense", "income", "debt", "sale"),
    },
    "Tesisat / teknik servis": {
        "title": "Servis işlerin bugün",
        "summary": "İşçilik tahsilatı, malzeme gideri ve iş tekliflerini öne aldık.",
        "focus": "Teklif · Gider · Müşteri hesabı",
        "actions": ("income", "expense", "debt", "sale"),
    },
    "Butik / perakende": {
        "title": "Mağazan bugün",
        "summary": "Hızlı satış, ürün stoğu ve müşteri bakiyelerini öne aldık.",
        "focus": "Hızlı satış · Stok · Veresiye",
        "actions": ("sale", "debt", "income", "expense"),
    },
    "Yeme içme": {
        "title": "İşletmen bugün",
        "summary": "Günlük satış, malzeme gideri ve mutfak kontrolünü öne aldık.",
        "focus": "Hızlı satış · Gider · Stok kontrolü",
        "actions": ("sale", "expense", "income", "debt"),
    },
    "Serbest meslek": {
        "title": "İşlerin bugün",
        "summary": "Müşteri tahsilatı, iş teklifi ve evrak takibini öne aldık.",
        "focus": "Gelen para · Teklif · Evrak",
        "actions": ("income", "expense", "debt", "sale"),
    },
    "Diğer": {
        "title": "İşletmen bugün",
        "summary": "Kasa, müşteriler ve stok araçlarını öne aldık.",
        "focus": "Kasa · Müşteriler · Stok",
        "actions": ("income", "expense", "debt", "sale"),
    },
}
SECTOR_REMINDER_HINTS = {
    "Bakkal / market": "Raf ve son kullanma tarihi kontrolü",
    "Berber / kuaför": "Ekipman bakımı ve sarf malzeme kontrolü",
    "Marangoz / mobilya": "Makine ve el aleti bakım kontrolü",
    "Tesisat / teknik servis": "Alet çantası ve servis randevusu kontrolü",
    "Butik / perakende": "Stok ve sezonluk ürün kontrolü",
    "Yeme içme": "Soğuk saklama ve mutfak ekipmanı kontrolü",
    "Serbest meslek": "Müşteri işi ve fatura evrakı kontrolü",
    "Diğer": "İşletme ekipmanı ve evrak kontrolü",
}


def show_profile(page, profile, submit):
    fields = {
        "business_name": ft.TextField(label="İşletme adı", value=profile.get("business_name", "")),
        "owner": ft.TextField(label="Ad soyad", value=profile.get("owner", "")),
        "email": ft.TextField(label="E-posta", value=profile.get("email", ""), keyboard_type=ft.KeyboardType.EMAIL),
        "sector": ft.Dropdown(
            label="İş kolu",
            value=profile.get("sector", SECTORS[0]),
            options=[ft.DropdownOption(text=item) for item in SECTORS],
        ),
        "legal_form": ft.Dropdown(
            label="İşletme türü",
            value=profile.get("legal_form", LEGAL_FORMS[0]),
            options=[ft.DropdownOption(text=item) for item in LEGAL_FORMS],
        ),
        "tax_office": ft.TextField(label="Vergi dairesi (isteğe bağlı)", value=profile.get("tax_office", "")),
        "tax_number": ft.TextField(label="Vergi / T.C. kimlik no (isteğe bağlı)", value=profile.get("tax_number", "")),
        "phone": ft.TextField(label="İş telefonu", value=profile.get("phone", ""), keyboard_type=ft.KeyboardType.PHONE),
        "address": ft.TextField(label="İşletme adresi", value=profile.get("address", ""), multiline=True, min_lines=2, max_lines=3),
    }

    async def save():
        values = {key: field.value or "" for key, field in fields.items()}
        if not values["business_name"].strip():
            fields["business_name"].error = "İşletme adını yaz."
            page.update()
            return
        if await submit(values):
            page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("İşletme profilini oluştur", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                width=360,
                controls=[
                    ft.Text("İş kolunu seçince ana ekranın kısayolları sana göre düzenlenir. Profil bu cihazda saklanır. Premium denemesi yalnızca e-posta doğrulandıktan sonra üyelik sunucusunda başlar.", color=MUTED, size=12),
                    *fields.values(),
                ],
            ),
            actions=[
                ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
                ft.Button(content="Profili kaydet", bgcolor=TEAL, color="white", on_click=save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )


def show_membership(page, membership, on_mode_change, on_auth_action, on_refresh, on_purchase=None):
    mode = membership.get("mode", "simple")
    plan_text = membership.get("membership_label", "Sunucu üyeliği doğrulanmadı")
    premium_active = membership.get("premium_access", False)
    signed_in = membership.get("signed_in", False)
    configured = membership.get("configured", False)
    email_field = ft.TextField(
        label="Nakitçe hesabı e-postası",
        value=membership.get("email", ""),
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    password_field = ft.TextField(label="Hesap parolası", password=True, can_reveal_password=True)
    message = ft.Text(membership.get("message", ""), color=MUTED, size=12)

    async def auth_action(action):
        await on_auth_action(action, email_field.value or "", password_field.value or "")
        page.pop_dialog()

    controls = [
        ft.Text("Premium erişimi yalnızca Nakitçe üyelik sunucusunun doğruladığı hesap veya Google Play aboneliğiyle açılır. Cihaz tarihi veya yerel sayaç hak vermez.", color=MUTED, size=12),
        ft.Text(plan_text, color=TEAL if premium_active else MUTED, weight=ft.FontWeight.W_600),
        message,
        ft.Text("Temel: ayda 30 hareket, 10 müşteri, 20 ürün ve 3 aktif hatırlatma. Premium: limitsiz kullanım, 12 aylık pasta grafik, POS ve teklif araçları, ekli belge saklama ve bulut eşitleme.", color=MUTED, size=12),
        ft.Text("Önerilen fiyat: 99,99 TL/ay veya 999,99 TL/yıl. Bunlar taslak fiyatlardır; gerçek fiyat Play kataloğundan okunmalıdır. Kullanıcının kendi Supabase bulut ücreti bu abonelikten ayrıdır.", color=INK, size=12),
    ]
    if not configured:
        controls.append(ft.Text("Üyelik servisi henüz bağlanmadı. Geliştirici Supabase URL ve public anon key ayarlanana kadar Premium kapalı kalır.", color="#8A641C", size=12))
    elif signed_in:
        controls.append(ft.Text(f"Hesap: {membership.get('email', '')}", color=INK, size=12))
        controls.append(ft.Row(wrap=True, controls=[
            ft.Button(content="Durumu sunucudan yenile", on_click=lambda e: on_refresh()),
            ft.TextButton(content="Oturumu kapat", on_click=lambda e: on_auth_action("sign_out", "", "")),
        ]))
    else:
        controls.extend([email_field, password_field, ft.Row(wrap=True, controls=[
            ft.Button(content="Hesap oluştur", on_click=lambda e: auth_action("sign_up"), bgcolor=TEAL, color="white"),
            ft.Button(content="Giriş yap", on_click=lambda e: auth_action("sign_in")),
        ])])
    controls.extend([
        ft.Text("Deneme cihazda başlatılmaz. E-posta doğrulandıktan sonra sunucu kendi saatiyle bir kez 30 günlük deneme yazar. İstersen Play Console'da abonelik deneme teklifi de tanımlayabilirsin.", color=MUTED, size=12),
        ft.Button(
            content="Google Play'den Premium satın al",
            on_click=lambda e: on_purchase() if on_purchase else None,
            disabled=on_purchase is None,
            tooltip="Satın alma belirteci Edge Function üzerinden doğrulanır. Ürün kimlikleri kesinleşene kadar köprü stub'tır.",
        ),
        ft.Text("Ekran modu", color=INK, weight=ft.FontWeight.W_600),
        ft.Row(wrap=True, controls=[
            ft.Button(content="Basit", disabled=mode == "simple", on_click=lambda e: on_mode_change("simple")),
            ft.Button(content="İleri seviye", disabled=not premium_active or mode == "advanced", on_click=lambda e: on_mode_change("advanced"), tooltip="Sunucuda doğrulanmış Premium gerekir"),
        ]),
        ft.Text("Nakitçe günlük işletme kayıt defteridir; resmî defter veya GİB e-Fatura hizmeti değildir. GİB işlemleri resmî portalda tamamlanır.", color=MUTED, size=12),
    ])
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Üyelik ve ekran modu", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, width=360, scroll=ft.ScrollMode.AUTO, controls=controls),
            actions=[ft.TextButton(content="Kapat", on_click=lambda e: page.pop_dialog())],
        )
    )


def show_reminder(page, submit, sector=""):
    suggested_title = SECTOR_REMINDER_HINTS.get(sector, "İşletme kontrolü")
    fields = {
        "title": ft.TextField(label="Hatırlatma başlığı", value=suggested_title),
        "date": ft.TextField(label="Tarih (YYYY-AA-GG)", hint_text="2026-12-31"),
        "note": ft.TextField(label="Not", multiline=True, min_lines=2, max_lines=3),
    }

    async def save():
        values = {key: field.value or "" for key, field in fields.items()}
        if not values["title"].strip() or not values["date"].strip():
            return
        if await submit(values):
            page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Hatırlatma ekle", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, controls=list(fields.values()), width=340, spacing=10),
            actions=[
                ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
                ft.Button(content="Kaydet", bgcolor=TEAL, color="white", on_click=save),
            ],
        )
    )
