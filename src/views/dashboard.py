from datetime import date

import flet as ft

from membership import premium_access
from reminders_engine import critical_alerts
from views.business import SECTOR_CONFIG, SECTOR_REMINDER_HINTS
from views.common import (
    INK,
    MINT,
    MUTED,
    RED,
    TEAL,
    alert_card,
    card,
    heading,
    metric_tile,
    money,
    section_label,
)
from views.pie_svg import pie_chart_data_uri


def build(records, actions, workspace=None):
    workspace = workspace or {"profile": {}, "mode": "simple", "reminders": []}
    profile = workspace.get("profile", {})
    sector = profile.get("sector", "Diğer")
    sector_config = SECTOR_CONFIG.get(sector, SECTOR_CONFIG["Diğer"])
    month = date.today().isoformat()[:7]
    monthly = [t for t in records["transactions"] if t.get("date", "").startswith(month)]
    income = sum(t["amount"] for t in monthly if t["type"] == "income")
    expenses = sum(t["amount"] for t in monthly if t["type"] == "expense")
    receivables = sum(c["balance"] for c in records["customers"])
    pending_pos = sum(p["net"] for p in records["pos"] if not p["paid"])
    low_stock = sum(1 for p in records["products"] if p["min_qty"] and p["qty"] <= p["min_qty"])
    alerts = critical_alerts(records, workspace)

    hero = ft.Container(
        padding=20,
        border_radius=24,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#0B1C2C", "#0F4C45", "#168F79"],
        ),
        shadow=ft.BoxShadow(blur_radius=24, color="#33000000", offset=ft.Offset(0, 10)),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Cebindeki kasa defteri", color="#9ED9CB", size=12, weight=ft.FontWeight.W_600),
                ft.Text(sector_config["title"], color="white", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    profile.get("business_name") or "Paranı doğru yönet, kârını gör.",
                    color="#D7F5EE",
                    size=14,
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(content="Aldım", on_click=actions["income"], bgcolor="#0F9B82", color="white"),
                        ft.Button(content="Verdim", on_click=actions["expense"], bgcolor=RED, color="white"),
                        ft.Button(content="Sesle / fişle kayıt", on_click=actions["intake"], bgcolor="white", color=INK),
                    ],
                ),
            ],
        ),
    )

    metrics = [
        metric_tile("Kasadaki para", money(records["cash_balance"]), "Bugünkü nakit", bgcolor=MINT, accent=TEAL, col={"xs": 6, "md": 3}),
        metric_tile("Alacakların", money(receivables), "Açık veresiye", bgcolor="#FFF5E2", accent="#A66A08", col={"xs": 6, "md": 3}),
        metric_tile("Bu ay aldım", money(income), "Gelen para", bgcolor="#EAF2FF", accent="#3565A8", col={"xs": 6, "md": 3}),
        metric_tile("Bu ay verdim", money(expenses), "Giden para", bgcolor="#FFF0EF", accent=RED, col={"xs": 6, "md": 3}),
    ]

    sector_action_controls = {
        "sale": ft.Button(content="Hızlı satış", on_click=actions["sale"], bgcolor=MINT, color=TEAL),
        "income": ft.Button(content="Aldım", on_click=actions["income"], bgcolor=TEAL, color="white"),
        "expense": ft.Button(content="Verdim", on_click=actions["expense"], bgcolor=RED, color="white"),
        "debt": ft.Button(content="Veresiye", on_click=actions["debt"], bgcolor="#FFF1D8", color=INK),
    }
    server_status = workspace.get("_server_membership_status")
    is_premium = premium_access(server_status)
    advanced_mode = workspace.get("mode") == "advanced" and is_premium
    visible_action_keys = sector_config["actions"] if advanced_mode else sector_config["actions"][:3]
    quick_actions = ft.Column(
        spacing=8,
        controls=[
            section_label("Günlük işler"),
            ft.Text(sector_config["summary"], color=MUTED, size=12),
            ft.Row(
                wrap=True,
                spacing=8,
                controls=[
                    *(sector_action_controls[key] for key in visible_action_keys),
                    ft.Button(content="GİB e-Arşiv", on_click=actions["open_gib"], bgcolor="#EAF2FF", color="#3565A8"),
                    *([ft.Button(content="Üyelik", on_click=actions["membership"])] if not advanced_mode else []),
                ],
            ),
        ],
    )

    alert_section = ft.Column(
        spacing=8,
        controls=[
            section_label("Kritik günler"),
            ft.Text(
                "Esnaf dilinden hatırlatmalar. Vergi tarihlerini kendi tebligatınla doğrula.",
                color=MUTED,
                size=11,
            ),
            *(
                [alert_card(item["title"], item["subtitle"], tone=item["tone"]) for item in alerts]
                if alerts
                else [card(ft.Text("Bugün kritik uyarı yok. Rahat nefes al.", color=MUTED, size=12))]
            ),
            ft.TextButton(content="+ Hatırlatma ekle", on_click=actions["add_reminder"]),
        ],
    )

    follow_ups = ft.Column(
        spacing=10,
        controls=[
            section_label("Takip et"),
            card(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            alignment=ft.Alignment.CENTER,
                            border_radius=14,
                            bgcolor="#FFF1D8",
                            content=ft.Text("₺", size=20, color="#A66A08", weight=ft.FontWeight.BOLD),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text("POS'tan beklenen", color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    f"{money(pending_pos)} · {len([p for p in records['pos'] if not p['paid']])} ödeme",
                                    color=MUTED,
                                    size=13,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            card(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            alignment=ft.Alignment.CENTER,
                            border_radius=14,
                            bgcolor="#FFF0EF",
                            content=ft.Text("!", size=20, color=RED, weight=ft.FontWeight.BOLD),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text("Azalan stok", color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(f"{low_stock} kalemde kritik seviye", color=MUTED, size=13),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )

    recent = sorted(records["transactions"], key=lambda t: t.get("date", ""), reverse=True)[:5]
    recent_cards = []
    for item in recent:
        positive = item["type"] == "income"
        is_debt = item["type"] == "debt"
        recent_cards.append(
            card(
                ft.Row(
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(item["title"], color=INK, weight=ft.FontWeight.W_600),
                                ft.Text(item["date"], color=MUTED, size=12),
                            ],
                        ),
                        ft.Text(
                            ("+ " if positive else ("Veresiye · " if is_debt else "− ")) + money(item["amount"]),
                            color=TEAL if positive else ("#A66A08" if is_debt else RED),
                            weight=ft.FontWeight.BOLD,
                        ),
                    ]
                )
            )
        )

    month_count = 12 if is_premium else 1
    current_month = date.today().replace(day=1)
    first_month_index = current_month.month - (month_count - 1)
    first_year = current_month.year + (first_month_index - 1) // 12
    first_month = (first_month_index - 1) % 12 + 1
    chart_start = f"{first_year:04d}-{first_month:02d}"
    chart_transactions = [item for item in records["transactions"] if item.get("date", "")[:7] >= chart_start]
    chart_income = sum(item.get("amount", 0) for item in chart_transactions if item.get("type") == "income")
    chart_expenses = sum(item.get("amount", 0) for item in chart_transactions if item.get("type") == "expense")
    chart_total = chart_income + chart_expenses
    visible_chart_values = [(label, value, color) for label, value, color in (("Gelen", chart_income, TEAL), ("Giden", chart_expenses, RED)) if value > 0]

    def _pct(value):
        return 0 if chart_total <= 0 else round(100 * value / chart_total)

    chart = ft.Image(
        src=pie_chart_data_uri(
            [(value, color) for _label, value, color in visible_chart_values] or [(1, "#DCE5E3")],
            size=210,
        ),
        width=210,
        height=210,
        fit=ft.BoxFit.CONTAIN,
        semantics_label="Gelir ve gider pasta grafiği",
    )
    period_label = "son 12 ay" if is_premium else "bu ay"
    chart_card = card(
        ft.Column(
            spacing=8,
            controls=[
                ft.Text("Para dağılımı", color=INK, weight=ft.FontWeight.W_700),
                ft.Text(f"Aldım / verdim payı · {period_label}", color=MUTED, size=11),
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        chart,
                        ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text("●", color=TEAL),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(f"Aldım · %{_pct(chart_income)}", color=MUTED, size=12),
                                                ft.Text(money(chart_income), color=INK, weight=ft.FontWeight.W_600),
                                            ],
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text("●", color=RED),
                                        ft.Column(
                                            spacing=2,
                                            controls=[
                                                ft.Text(f"Verdim · %{_pct(chart_expenses)}", color=MUTED, size=12),
                                                ft.Text(money(chart_expenses), color=INK, weight=ft.FontWeight.W_600),
                                            ],
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    )

    has_any_data = bool(records["transactions"] or records["customers"] or records["products"])
    welcome = card(
        ft.Column(
            spacing=8,
            controls=[
                ft.Text("Hoş geldin! 3 adımda başla", color=INK, weight=ft.FontWeight.BOLD, size=16),
                ft.Text("1) Kasadaki parayı yaz   2) İlk Aldım / Verdim kaydını gir   3) Veresiye veren müşterini ekle. Kayıtların girdikçe burada özetlenir.", color=MUTED, size=12),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(content="Kasadaki parayı yaz", on_click=actions["opening"], bgcolor=TEAL, color="white"),
                        ft.Button(content="Müşteri ekle", on_click=actions["add"]),
                    ],
                ),
            ],
        ),
        bgcolor="#FFF9ED",
    )
    show_follow_ups = bool(pending_pos or low_stock)

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=16,
        controls=[
            hero,
            *([] if has_any_data else [welcome]),
            heading("Nakit özeti", "Muhasebe değil — paran nerede, kârın ne."),
            ft.ResponsiveRow(controls=metrics, spacing=12, run_spacing=12),
            *([chart_card] if chart_total > 0 else []),
            alert_section,
            quick_actions,
            *([follow_ups] if show_follow_ups else []),
            ft.Text(
                f"Öneri: {SECTOR_REMINDER_HINTS.get(sector, 'İşletme kontrolü')}",
                color=MUTED,
                size=11,
            ),
            section_label("Son hareketler"),
            *(recent_cards or [card(ft.Text("Henüz hareket yok.", color=MUTED))]),
            ft.TextButton(content="Gizlilik, KVKK ve yasal bilgiler", on_click=actions["legal"]),
        ],
    )
