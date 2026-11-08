import flet as ft

from membership import current_plan, membership_summary
from membership_config import SUPPORT_EMAIL
from views.common import INK, MUTED, TEAL, action_button, card, heading, money, section_label


def build(records, actions, sync_state, workspace=None):
    workspace = workspace or {"profile": {}, "mode": "simple", "reminders": []}
    profile = workspace.get("profile", {})
    profile_label = profile.get("business_name", "İşletme profilini oluştur")
    server_status = workspace.get("_server_membership_status")
    plan = current_plan(server_status)
    membership_label = membership_summary(server_status)
    pos_rows = []
    for item in sorted(records["pos"], key=lambda p: p["date"]):
        pos_rows.append(
            card(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            alignment=ft.Alignment.CENTER,
                            border_radius=13,
                            bgcolor="#FFF5E2",
                            content=ft.Text("₺", color="#A66A08", weight=ft.FontWeight.BOLD),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(item["bank"], color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    f"{item['date']} · %{item['rate']} kesinti · {item['days']} gün",
                                    color=MUTED,
                                    size=12,
                                ),
                                ft.Text(
                                    f"Brüt {money(item['gross'])} → net {money(item['net'])}",
                                    color=INK,
                                    size=12,
                                ),
                            ],
                        ),
                        ft.Button(
                            content="Hesaba geçti" if not item["paid"] else "Geri al",
                            on_click=lambda e, p=item: actions["toggle_pos"](p),
                            bgcolor="#E8F7F2" if not item["paid"] else "#F2F5F4",
                            color=TEAL if not item["paid"] else INK,
                        ),
                    ]
                )
            )
        )

    quote_rows = []
    for quote in reversed(records["quotes"]):
        total = quote["materials"] + quote["labor"]
        quote_rows.append(
            card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=3,
                                    controls=[
                                        ft.Text(quote["title"], color=INK, weight=ft.FontWeight.W_600),
                                        ft.Text(f"{quote['customer']} · {quote['date']}", color=MUTED, size=12),
                                    ],
                                ),
                                ft.Text(money(total), color=TEAL, weight=ft.FontWeight.BOLD),
                            ]
                        ),
                        ft.Text(
                            f"Malzeme {money(quote['materials'])} · İşçilik {money(quote['labor'])}",
                            color=MUTED,
                            size=12,
                        ),
                        ft.Button(
                            content="Teklif PDF'i",
                            on_click=lambda e, q=quote: actions["quote_pdf"](q),
                            bgcolor="#F2F5F4",
                            color=INK,
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
            heading("İş araçları", "Ücretsiz kasa defteri + Premium güç araçları."),
            section_label("İşletme ve üyelik"),
            card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(profile_label, color=INK, weight=ft.FontWeight.W_600),
                        ft.Text(
                            " · ".join(
                                value for value in [profile.get("legal_form", ""), profile.get("sector", "")] if value
                            )
                            or "Profilini tamamla — kısayollar işine göre şekillenir.",
                            color=MUTED,
                            size=12,
                        ),
                        ft.Text(
                            f"Üyelik: {membership_label}",
                            color=TEAL if plan in {"trial", "premium"} else MUTED,
                            size=12,
                        ),
                        ft.Text(
                            "Ücretsiz: ayda 30 Aldım/Verdim, ayda 8 WhatsApp. Veresiye sınırsız. "
                            "Premium: sınırsız kasa ve WhatsApp, bulut yedek, POS, teklif, banka CSV.",
                            color=MUTED,
                            size=11,
                        ),
                        ft.Row(
                            wrap=True,
                            controls=[
                                action_button("Profili düzenle", actions["edit_profile"], primary=True),
                                action_button("Üyelik / Premium", actions["membership"]),
                            ],
                        ),
                    ],
                )
            ),
            section_label("Kart / POS tahsilat takibi"),
            card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Telefonunu POS yapma iddiası yok", color=INK, weight=ft.FontWeight.W_700),
                        ft.Text(
                            "Temassız SoftPOS için banka lisanslı cihaz gerekir. Burada karttan kesilen "
                            "satışın ne zaman hesaba geçeceğini ve kesintiyi takip edersin — çalışır, abartısız.",
                            color=INK,
                            size=12,
                        ),
                        action_button("+ Kart satışı kaydet", actions["add_pos"], primary=True),
                    ],
                ),
                bgcolor="#FFF9ED",
            ),
            *(pos_rows or [card(ft.Text("Bekleyen POS yok.", color=MUTED))]),
            section_label("Banka ekstresi (CSV)"),
            card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Hesap hareketlerini içe aktar", color=INK, weight=ft.FontWeight.W_700),
                        ft.Text(
                            "Bankanın indirdiği CSV'yi seç. Tarih, açıklama, tutar / alacak-borç sütunları okunur. "
                            "Açık bankacılık bağlantısı yoktur — dosya cihazda işlenir.",
                            color=MUTED,
                            size=12,
                        ),
                        action_button("CSV içe aktar", actions["import_bank"], primary=True),
                    ],
                ),
                bgcolor="#F0F6FF",
            ),
            section_label("Hızlı teklifler"),
            action_button("+ Teklif oluştur", actions["add_quote"]),
            *(quote_rows or [card(ft.Text("Henüz teklif yok.", color=MUTED))]),
            section_label("Mali müşavire gönder"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Ay sonu raporu", color=INK, weight=ft.FontWeight.W_600),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                action_button("Excel / CSV", actions["export_csv"], primary=True),
                                action_button("PDF raporu", actions["export_pdf"]),
                            ],
                        ),
                    ],
                )
            ),
            section_label("Nakitçe bulutu"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(sync_state.get("message", "Bulut için giriş yap."), color=INK, size=12),
                        ft.Text(
                            "Veritabanı Miras Teknoloji’nin Nakitçe projesindedir. "
                            "Kendi Supabase hesabı açmana gerek yok. "
                            "Nakitçe hesabınla giriş yap → Premium ile eşitle. "
                            "Kayıtlar hesabına özeldir (RLS).",
                            color=INK,
                            size=12,
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                action_button("Nakitçe hesabı", actions["sync_setup"], primary=True),
                                action_button("Şimdi eşitle", actions["sync_now"]),
                            ],
                        ),
                        *(
                            [
                                ft.Text("Çakışma var — hangi kopyanın kalacağını seç.", color="#A66A08", size=12),
                                ft.Row(
                                    wrap=True,
                                    spacing=8,
                                    controls=[
                                        action_button("Bu cihazı yükle", actions["sync_upload"], primary=True),
                                        action_button("Buluttan al", actions["sync_download"]),
                                    ],
                                ),
                            ]
                            if sync_state.get("conflict")
                            else []
                        ),
                    ],
                ),
                bgcolor="#F0F6FF",
            ),
            section_label("GİB e-Arşiv"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Resmi portal + hazırlık panosu", color=INK, weight=ft.FontWeight.W_700),
                        ft.Text(
                            "Nakitçe fatura kesmez ve GİB şifresi istemez. Profil bilgilerini panoya kopyala, "
                            "portalı aç, faturayı GİB'de tamamla.",
                            color=INK,
                            size=12,
                        ),
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("1 · Hazırlık metnini kopyala", color=INK, size=12),
                                ft.Text("2 · GİB e-Arşiv'e güvenli giriş yap", color=INK, size=12),
                                ft.Text("3 · Bilgileri yapıştırıp faturayı oluştur", color=INK, size=12),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                action_button("Hazırlığı kopyala", actions["gib_draft"], primary=True),
                                action_button("GİB portalını aç ↗", actions["open_gib"]),
                            ],
                        ),
                        ft.Text("Yükümlülük ve tutar sınırları için GİB'in güncel metnini esas al.", color=INK, size=11),
                    ],
                ),
                bgcolor="#FFF9ED",
            ),
            *(
                [
                    section_label("Örnek veri"),
                    card(
                        ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("Örnek işletme modu açık", color=INK, weight=ft.FontWeight.W_700),
                                ft.Text(
                                    "Bu kayıtlar tanıtım içindir. Temizleyince boş kasa defteri kalır.",
                                    color=MUTED,
                                    size=12,
                                ),
                                action_button("Örnek veriyi temizle", actions["clear_demo"], primary=True),
                            ],
                        ),
                        bgcolor="#E8F7F2",
                    ),
                ]
                if workspace.get("demo_mode") and "clear_demo" in actions
                else []
            ),
            card(
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            "İnternet yokken kayıtlar bu cihazda kalır. SoftPOS / kart okuma vaadi yoktur.",
                            color=MUTED,
                            size=12,
                        ),
                        ft.Text(
                            f"Destek: {SUPPORT_EMAIL}" if SUPPORT_EMAIL else "Destek: Araçlar → Üyelik",
                            color=MUTED,
                            size=12,
                        ),
                    ],
                )
            ),
        ],
    )
