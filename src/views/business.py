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


def show_membership(page, membership, on_mode_change, on_auth_action, on_refresh, on_purchase=None, billing_available=False, on_redeem=None, on_delete_account=None, on_legal=None, on_web_pay=None, price_text=""):
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
        ft.Container(
            padding=14,
            border_radius=16,
            bgcolor="#E8F7F2",
            content=ft.Column(
                spacing=6,
                tight=True,
                controls=[
                    ft.Text("Serbest bölge · ücretsiz", color=TEAL, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Aldım/Verdim, veresiye, WhatsApp PDF, sesle kayıt, fiş OCR, stok, kritik günler.",
                        color=INK,
                        size=12,
                    ),
                ],
            ),
        ),
        ft.Container(
            padding=14,
            border_radius=16,
            bgcolor="#FFF9ED",
            content=ft.Column(
                spacing=6,
                tight=True,
                controls=[
                    ft.Text("Premium", color=INK, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "POS takibi, teklif, banka CSV, Nakitçe bulutu (Miras), 12 aylık grafik, ileri ekran.",
                        color=INK,
                        size=12,
                    ),
                    ft.Text(f"{price_text} (güncel fiyat satın alma ekranında görünür)." if price_text else "", color=INK, size=11),
                ],
            ),
        ),
        ft.Text(plan_text, color=TEAL if premium_active else MUTED, weight=ft.FontWeight.W_600),
        message,
    ]
    if not configured:
        controls.append(
            ft.Text(
                "Üyelik servisi bağlı değil. Temel özellikler çalışır; Premium sunucu + Play sonrası açılır.",
                color="#8A641C",
                size=12,
            )
        )
    elif signed_in:
        controls.append(ft.Text(f"Hesap: {membership.get('email', '')}", color=INK, size=12))
        code_field = ft.TextField(label="Aktivasyon kodu (XXXX-XXXX-XXXX)", capitalization=ft.TextCapitalization.CHARACTERS)

        async def redeem(e):
            if on_redeem:
                await on_redeem(code_field.value or "")
                page.pop_dialog()

        controls.append(
            ft.Row(
                wrap=True,
                controls=[
                    code_field,
                    ft.Button(content="Kodu kullan", on_click=redeem, bgcolor=TEAL, color="white"),
                ],
            )
        )
        if on_web_pay:
            controls.append(ft.Button(content="Web'den Premium satın al", on_click=lambda e: on_web_pay()))
        controls.append(
            ft.Row(
                wrap=True,
                controls=[
                    ft.Button(content="Durumu yenile", on_click=lambda e: on_refresh()),
                    ft.TextButton(content="Oturumu kapat", on_click=lambda e: on_auth_action("sign_out", "", "")),
                    ft.TextButton(content="Hesabımı sil", on_click=lambda e: on_delete_account() if on_delete_account else None),
                ],
            )
        )
    else:
        controls.extend(
            [
                email_field,
                password_field,
                ft.Row(
                    wrap=True,
                    controls=[
                        ft.Button(content="Hesap oluştur", on_click=lambda e: auth_action("sign_up"), bgcolor=TEAL, color="white"),
                        ft.Button(content="Giriş yap", on_click=lambda e: auth_action("sign_in")),
                    ],
                ),
            ]
        )
    if billing_available and on_purchase:
        controls.append(
            ft.Button(content="Google Play'den Premium al", on_click=lambda e: on_purchase(), bgcolor=TEAL, color="white")
        )
    if on_legal:
        controls.append(ft.TextButton(content="Gizlilik, KVKK ve yasal bilgiler", on_click=lambda e: on_legal()))
    controls.extend(
        [
            ft.Text("Ekran modu", color=INK, weight=ft.FontWeight.W_600),
            ft.Row(
                wrap=True,
                controls=[
                    ft.Button(content="Basit", disabled=mode == "simple", on_click=lambda e: on_mode_change("simple")),
                    ft.Button(
                        content="İleri seviye",
                        disabled=not premium_active or mode == "advanced",
                        on_click=lambda e: on_mode_change("advanced"),
                    ),
                ],
            ),
            ft.Text("Nakitçe SoftPOS veya resmî GİB faturası değildir.", color=MUTED, size=12),
        ]
    )
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Üyelik · Serbest bölge", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, width=360, scroll=ft.ScrollMode.AUTO, controls=controls),
            actions=[ft.TextButton(content="Kapat", on_click=lambda e: page.pop_dialog())],
        )
    )


LEGAL_TEXT = (
    "Nakitçe bir işletme kasa/veresiye takip aracıdır. Resmî defter, e-Fatura/e-Arşiv, e-Defter, "
    "yazar kasa veya ÖKC yerine geçmez; vergi beyanı ve belge düzeni için mali müşavirine danış.\n\n"
    "Vergi Usul Kanunu'na göre ticari defter ve belgelerin 5 yıl saklanması gerekir. Asıl belgelerini "
    "(fatura, fiş) saklamaya devam et; Nakitçe'deki kayıtlar yardımcı dijital bir takip içindir.\n\n"
    "KVKK: Kayıtların (müşteri adı, telefon, tutarlar) bu cihazda saklanır. Üyelik e-postan ve bulut eşitlemesini "
    "açarsan kayıtların Nakitçe sunucusuna (Supabase) şifreli bağlantıyla yüklenir. Fiş fotoğrafı okuma "
    "(OCR) özelliğini kullanırsan görsel, metne çevrilmesi için internetteki bir OCR servisine gönderilir; "
    "fotoğraf eklemen bu aktarımı kabul ettiğin anlamına gelir, istemezsen bilgiyi elle gir. Müşterilerinin kişisel verilerini işlerken kendi aydınlatma "
    "yükümlülüğünden sen sorumlusun.\n\n"
    "Verilerini istediğin zaman Araçlar'dan dışa aktarabilir, Üyelik ekranından hesabını ve bulut verilerini "
    "kalıcı olarak silebilirsin."
)


def show_legal(page, privacy_url="", on_open_url=None):
    actions = [ft.TextButton(content="Kapat", on_click=lambda e: page.pop_dialog())]
    if privacy_url and on_open_url:
        actions.insert(0, ft.TextButton(content="Gizlilik politikası", on_click=lambda e: on_open_url(privacy_url)))
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Gizlilik ve yasal bilgiler", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, width=360, scroll=ft.ScrollMode.AUTO, controls=[ft.Text(LEGAL_TEXT, color=MUTED, size=12)]),
            actions=actions,
        )
    )


CONSENT_SUMMARY = (
    "Nakitçe cebindeki kasa defteridir; resmî defter veya e-Fatura yerine geçmez. "
    "Kayıtların bu cihazda saklanır. Üyelik / bulut veya fiş fotoğrafı (OCR) kullanırsan "
    "ilgili veriler sunucuya gider — ayrıntılar gizlilik metninde."
)


def show_consent(page, on_accept, privacy_url="", on_open_url=None, on_legal=None):
    async def accept(e):
        page.pop_dialog()
        await on_accept()

    actions = [
        ft.Button(content="Devam et", bgcolor=TEAL, color="white", on_click=accept),
    ]
    if on_legal:
        actions.insert(0, ft.TextButton(content="Ayrıntılar", on_click=lambda e: on_legal()))
    elif privacy_url and on_open_url:
        actions.insert(0, ft.TextButton(content="Gizlilik", on_click=lambda e: on_open_url(privacy_url)))

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Nakitçe'ye hoş geldin", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                width=360,
                spacing=10,
                controls=[
                    ft.Text("Aldım / Verdim ile hemen kayda başlayabilirsin.", color=INK, size=13, weight=ft.FontWeight.W_600),
                    ft.Text(CONSENT_SUMMARY, color=MUTED, size=12),
                    ft.Text("İşletme profilini sonra Araçlar'dan tamamlayabilirsin.", color=MUTED, size=11),
                ],
            ),
            actions=actions,
        )
    )


def show_reminder(page, submit, sector=""):
    from datetime import date, timedelta

    suggested_title = SECTOR_REMINDER_HINTS.get(sector, "İşletme kontrolü")
    presets = [
        ("Yarın KDV günü olabilir", 1, "Tebligatını kontrol et — resmî tarih GİB'e göredir."),
        ("Komşunun / müşterinin borç vadesi", 0, "Açık hesabı olan müşteriyi ara veya WhatsApp'la."),
        ("BA-BS / ay sonu evrak", max(0, (date.today().replace(day=28) - date.today()).days), "Ba-Bs yükümlülüğün varsa mali müşavirinle doğrula."),
        (suggested_title, 7, "Sektörüne özel kontrol."),
    ]
    fields = {
        "title": ft.TextField(label="Hatırlatma başlığı", value=presets[0][0]),
        "date": ft.TextField(label="Tarih (YYYY-AA-GG)", value=(date.today() + timedelta(days=1)).isoformat()),
        "note": ft.TextField(label="Not", value=presets[0][2], multiline=True, min_lines=2, max_lines=3),
    }

    def apply_preset(title, days, note):
        fields["title"].value = title
        fields["date"].value = (date.today() + timedelta(days=days)).isoformat()
        fields["note"].value = note
        page.update()

    async def save():
        values = {key: field.value or "" for key, field in fields.items()}
        if not values["title"].strip() or not values["date"].strip():
            return
        if await submit(values):
            page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Kritik gün hatırlatması", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                width=340,
                spacing=10,
                controls=[
                    ft.Text("Hazır esnaf dili:", color=MUTED, size=12),
                    ft.Row(
                        wrap=True,
                        spacing=6,
                        controls=[
                            ft.TextButton(
                                content=title[:28],
                                on_click=lambda e, t=title, d=days, n=note: apply_preset(t, d, n),
                            )
                            for title, days, note in presets
                        ],
                    ),
                    *fields.values(),
                ],
            ),
            actions=[
                ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
                ft.Button(content="Kaydet", bgcolor=TEAL, color="white", on_click=save),
            ],
        )
    )
