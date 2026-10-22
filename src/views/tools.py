import flet as ft

from membership import current_plan, membership_summary
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
                        ft.Container(width=40, height=40, alignment=ft.Alignment.CENTER, border_radius=13, bgcolor="#FFF5E2", content=ft.Text("₺", color="#A66A08", weight=ft.FontWeight.BOLD)),
                        ft.Column(expand=True, spacing=3, controls=[ft.Text(item["bank"], color=INK, weight=ft.FontWeight.W_600), ft.Text(f"{item['date']} · %{item['rate']} kesinti · {item['days']} gün", color=MUTED, size=12), ft.Text(f"Brüt {money(item['gross'])} → net {money(item['net'])}", color=INK, size=12)]),
                        ft.Button(content="Geldi" if not item["paid"] else "Geri al", on_click=lambda e, p=item: actions["toggle_pos"](p), bgcolor="#E8F7F2" if not item["paid"] else "#F2F5F4", color=TEAL if not item["paid"] else INK),
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
                        ft.Row(controls=[ft.Column(expand=True, spacing=3, controls=[ft.Text(quote["title"], color=INK, weight=ft.FontWeight.W_600), ft.Text(f"{quote['customer']} · {quote['date']}", color=MUTED, size=12)]), ft.Text(money(total), color=TEAL, weight=ft.FontWeight.BOLD)]),
                        ft.Text(f"Malzeme {money(quote['materials'])} · İşçilik {money(quote['labor'])}", color=MUTED, size=12),
                        ft.Button(content="Teklif PDF'i hazırla", on_click=lambda e, q=quote: actions["quote_pdf"](q), bgcolor="#F2F5F4", color=INK),
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
            heading("İş araçları", "İşletme profili, raporlar ve günlük araçlar."),
            section_label("İşletme bilgileri"),
            card(
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(profile_label, color=INK, weight=ft.FontWeight.W_600),
                        ft.Text(
                            " · ".join(value for value in [profile.get("legal_form", ""), profile.get("sector", "")] if value)
                            or "Rapor başlığı ve işine uygun hatırlatmalar için profilini tamamla.",
                            color=MUTED,
                            size=12,
                        ),
                        ft.Text(f"Üyelik: {membership_label}", color=TEAL if plan in {"trial", "premium"} else MUTED, size=12),
                        ft.Row(
                            wrap=True,
                            controls=[
                                action_button("İşletme profilini düzenle", actions["edit_profile"], primary=True),
                                action_button("Üyelik / Premium", actions["membership"]),
                            ],
                        ),
                    ],
                )
            ),
            section_label("POS'tan gelecek"),
            action_button("+ POS ödemesi ekle", actions["add_pos"], primary=True),
            *(pos_rows or [card(ft.Text("Bekleyen POS ödemesi yok.", color=MUTED))]),
            section_label("Hızlı teklifler"),
            action_button("+ Teklif oluştur", actions["add_quote"]),
            *(quote_rows or [card(ft.Text("Henüz teklif hazırlanmamış.", color=MUTED))]),
            section_label("Mali müşavire gönder"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Ay sonu raporunu dışa aktar", color=INK, weight=ft.FontWeight.W_600),
                        ft.Text("Excel'de açılabilen CSV veya yazdırmaya uygun PDF raporu oluştur.", color=MUTED, size=12),
                        ft.Row(wrap=True, spacing=8, controls=[action_button("Excel / CSV", actions["export_csv"], primary=True), action_button("PDF raporu", actions["export_pdf"])]),
                    ]
                )
            ),
            section_label("Bulut eşitlemesi"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text(sync_state.get("message", "Supabase bağlantısı ayarlanmadı."), color=INK, size=12),
                        ft.Text("Veriler cihazda çalışmaya devam eder. Eşitleme için kendi Supabase projenin URL ve public anon key bilgilerini gir; hesap parolan saklanmaz.", color=MUTED, size=12),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                action_button("Supabase hesabını bağla", actions["sync_setup"], primary=True),
                                action_button("Şimdi eşitle", actions["sync_now"]),
                            ],
                        ),
                        *(
                            [
                                ft.Text("İki cihazda da değişiklik var. Veri kaybını önlemek için eşitleme durduruldu; hangi kopyanın kullanılacağını seç.", color="#A66A08", size=12),
                                ft.Row(
                                    wrap=True,
                                    spacing=8,
                                    controls=[
                                        action_button("Bu cihazı buluta yükle", actions["sync_upload"], primary=True),
                                        action_button("Buluttakini bu cihaza al", actions["sync_download"]),
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
            section_label("GİB e-Arşiv faturası"),
            card(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Faturanı resmi GİB portalında oluştur", color=INK, weight=ft.FontWeight.W_600),
                        ft.Text("Portal girişini ve varsa SMS onayını doğrudan GİB sayfasında yap. Nakitçe kullanıcı adı, parola veya onay kodu istemez ve bunları kaydetmez.", color=MUTED, size=12),
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text("1 · GİB portalına güvenli şekilde giriş yap.", color=INK, size=12),
                                ft.Text("2 · Müşteri ve satış bilgilerini girip faturayı oluştur.", color=INK, size=12),
                                ft.Text("3 · Belgeyi GİB'den indir; müşterine WhatsApp veya e-posta ile gönder.", color=INK, size=12),
                            ],
                        ),
                        action_button("GİB e-Arşiv portalını aç ↗", actions["open_gib"], primary=True),
                        ft.Text("Belge türü, tutar sınırları ve yükümlülükler için GİB'in güncel yönlendirmesini esas al.", color="#8A641C", size=11),
                    ],
                ),
                bgcolor="#FFF9ED",
            ),
            card(ft.Text("İnternet yokken kayıtlar bu cihazda tutulur. Bulut eşitlemesi isteğe bağlıdır; bağlantı gelince son kayıtlar eşitlenir.", color=MUTED, size=12)),
        ],
    )
