from datetime import date

import flet as ft

from membership import premium_access
from views.business import SECTOR_CONFIG, SECTOR_REMINDER_HINTS
from views.common import INK, MINT, MUTED, RED, TEAL, card, heading, money, section_label
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

    metric_items = [
        ("Kasadaki para", money(records["cash_balance"]), "Bugünkü nakit durumun", MINT, TEAL),
        ("Müşterilerden alacağın", money(receivables), "Açık veresiye bakiyesi", "#FFF5E2", "#A66A08"),
        ("Bu ay gelen para", money(income), "Kayıtlı gelir hareketleri", "#EAF2FF", "#3565A8"),
        ("Bu ay giden para", money(expenses), "Kayıtlı gider hareketleri", "#FFF0EF", RED),
    ]
    metrics = [
        card(
            ft.Column(
                spacing=7,
                controls=[
                    ft.Text(label, size=13, color=MUTED),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=INK),
                    ft.Text(caption, size=12, color=accent),
                ],
            ),
            bgcolor=bg,
            col={"xs": 6, "md": 3},
        )
        for label, value, caption, bg, accent in metric_items
    ]

    sector_action_controls = {
        "sale": ft.Button(content="Hızlı satış / hizmet", on_click=actions["sale"], bgcolor=MINT, color=TEAL),
        "income": ft.Button(content="Para geldi", on_click=actions["income"], bgcolor=TEAL, color="white"),
        "expense": ft.Button(content="Para çıktı", on_click=actions["expense"], bgcolor=INK, color="white"),
        "debt": ft.Button(content="Veresiye ekle", on_click=actions["debt"], bgcolor="#FFF1D8", color=INK),
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
                    ft.Button(content="e-Arşiv fatura", on_click=actions["open_gib"], bgcolor="#EAF2FF", color="#3565A8"),
                    *([ft.Button(content="Üyelik ve ekran modu", on_click=actions["membership"])] if not advanced_mode else []),
                ],
            ),
        ],
    )

    reminders = ft.Column(
        spacing=10,
        controls=[
            section_label("Takip etmen gerekenler"),
            card(
                ft.Row(
                    controls=[
                        ft.Container(width=42, height=42, alignment=ft.Alignment.CENTER, border_radius=14, bgcolor="#FFF1D8", content=ft.Text("₺", size=20, color="#A66A08", weight=ft.FontWeight.BOLD)),
                        ft.Column(expand=True, spacing=3, controls=[ft.Text("POS'tan beklenen", color=INK, weight=ft.FontWeight.W_600), ft.Text(f"{money(pending_pos)} · {len([p for p in records['pos'] if not p['paid']])} ödeme", color=MUTED, size=13)]),
                        ft.Text("›", size=24, color=MUTED),
                    ],
                ),
            ),
            card(
                ft.Row(
                    controls=[
                        ft.Container(width=42, height=42, alignment=ft.Alignment.CENTER, border_radius=14, bgcolor="#FFF0EF", content=ft.Text("!", size=20, color=RED, weight=ft.FontWeight.BOLD)),
                        ft.Column(expand=True, spacing=3, controls=[ft.Text("Azalan stok", color=INK, weight=ft.FontWeight.W_600), ft.Text(f"{low_stock} üründe kritik seviyeye yaklaşıldı", color=MUTED, size=13)]),
                        ft.Text("›", size=24, color=MUTED),
                    ],
                ),
            ),
        ],
    )

    recent = sorted(records["transactions"], key=lambda t: t.get("date", ""), reverse=True)[:4]
    recent_cards = []
    for item in recent:
        positive = item["type"] == "income"
        is_debt = item["type"] == "debt"
        recent_cards.append(
            card(
                ft.Row(
                    controls=[
                        ft.Column(expand=True, spacing=3, controls=[ft.Text(item["title"], color=INK, weight=ft.FontWeight.W_600), ft.Text(item["date"], color=MUTED, size=12)]),
                        ft.Text(("+ " if positive else ("Veresiye · " if is_debt else "− ")) + money(item["amount"]), color=TEAL if positive else ("#A66A08" if is_debt else RED), weight=ft.FontWeight.BOLD),
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
    chart_transactions = [
        item for item in records["transactions"]
        if item.get("date", "")[:7] >= chart_start
    ]
    chart_income = sum(item.get("amount", 0) for item in chart_transactions if item.get("type") == "income")
    chart_expenses = sum(item.get("amount", 0) for item in chart_transactions if item.get("type") == "expense")
    chart_total = chart_income + chart_expenses
    chart_values = [("Gelen para", chart_income, TEAL), ("Giden para", chart_expenses, RED)]
    visible_chart_values = [(label, value, color) for label, value, color in chart_values if value > 0]

    def _pct(value):
        if chart_total <= 0:
            return 0
        return round(100 * value / chart_total)

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
                ft.Text("Para dağılımı · pasta grafik", color=INK, weight=ft.FontWeight.W_600),
                ft.Text(f"Gelir ve gider payı · {period_label}", color=MUTED, size=11),
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        chart,
                        ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(controls=[ft.Text("●", color=TEAL), ft.Column(spacing=2, controls=[ft.Text(f"Gelen para · %{_pct(chart_income)}", color=MUTED, size=12), ft.Text(money(chart_income), color=INK, weight=ft.FontWeight.W_600)])]),
                                ft.Row(controls=[ft.Text("●", color=RED), ft.Column(spacing=2, controls=[ft.Text(f"Giden para · %{_pct(chart_expenses)}", color=MUTED, size=12), ft.Text(money(chart_expenses), color=INK, weight=ft.FontWeight.W_600)])]),
                                *([ft.Text("Henüz bu dönemde kayıt yok", color=MUTED, size=11)] if not visible_chart_values else []),
                            ],
                        ),
                    ],
                ),
            ],
        )
    )

    upcoming = []
    for item in workspace.get("reminders", []):
        try:
            due = date.fromisoformat(item.get("date", ""))
        except ValueError:
            continue
        days_left = (due - date.today()).days
        upcoming.append((days_left, item))
    upcoming.sort(key=lambda pair: pair[0])
    reminder_cards = []
    for days_left, item in upcoming[:3]:
        date_label = "Gecikti" if days_left < 0 else ("Bugün" if days_left == 0 else f"{days_left} gün kaldı")
        reminder_cards.append(
            card(
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.EVENT, color=RED if days_left <= 3 else TEAL),
                        ft.Column(expand=True, spacing=2, controls=[ft.Text(item.get("title", "Hatırlatma"), color=INK, weight=ft.FontWeight.W_600), ft.Text(f"{item.get('date', '')} · {date_label}", color=MUTED, size=12)]),
                    ]
                )
            )
        )
    reminder_section = ft.Column(
        spacing=8,
        controls=[
            ft.Row(controls=[section_label("İşine göre hatırlatmalar"), ft.TextButton(content="+ Ekle", on_click=actions["add_reminder"])]),
            ft.Text(
                f"Öneri: {SECTOR_REMINDER_HINTS.get(workspace.get('profile', {}).get('sector', ''), 'İşletme ekipmanı ve evrak kontrolü')}. Resmî vergi ve ruhsat tarihlerini kendi tebligatından doğrula.",
                color=MUTED,
                size=11,
            ),
            *(reminder_cards or [card(ft.Text("Henüz tarihli hatırlatma yok. İşletmene özel bir tarih ekleyebilirsin.", color=MUTED, size=12))]),
        ],
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=16,
        controls=[
            heading(sector_config["title"], profile.get("business_name") or "İşinin özeti burada."),
            ft.Container(padding=14, border_radius=14, bgcolor="#EAF2FF", content=ft.Text(records.get("notice", ""), color="#355578", size=12)),
            ft.ResponsiveRow(controls=metrics, spacing=12, run_spacing=12),
            chart_card,
            quick_actions,
            reminder_section,
            reminders,
            section_label("Son hareketler"),
            *(recent_cards or [card(ft.Text("Henüz hareket yok.", color=MUTED))]),
        ],
    )
