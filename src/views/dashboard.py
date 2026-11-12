from datetime import date

import flet as ft

from free_quota import (
    FREE_CASH_OPS_MONTHLY,
    FREE_WHATSAPP_MONTHLY,
    cash_ops_used,
    day_totals,
    month_collected,
    whatsapp_used,
)
from membership import premium_access
from reminders_engine import collection_queue, critical_alerts
from views.business import SECTOR_CONFIG, SECTOR_REMINDER_HINTS
from views.common import (
    AMBER,
    AMBER_SOFT,
    INK,
    MINT,
    MUTED,
    RED,
    TEAL,
    WHITE,
    alert_card,
    card,
    empty_state,
    metric_tile,
    money,
    primary_cta,
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
    alerts = critical_alerts(records, workspace)[:3]
    today = date.today()
    server_status = workspace.get("_server_membership_status")
    is_premium = premium_access(server_status)
    cash_used = cash_ops_used(records.get("transactions"), today)
    wa_used = whatsapp_used(workspace, today)
    quota_line = (
        "Premium · sınırsız kasa ve WhatsApp"
        if is_premium
        else f"Ücretsiz · kasa {min(cash_used, FREE_CASH_OPS_MONTHLY)}/{FREE_CASH_OPS_MONTHLY} · WA {min(wa_used, FREE_WHATSAPP_MONTHLY)}/{FREE_WHATSAPP_MONTHLY}"
    )

    hero = ft.Container(
        padding=20,
        border_radius=28,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#0B1C2C", "#0F4C45", "#168F79"],
        ),
        shadow=ft.BoxShadow(blur_radius=28, color="#33000000", offset=ft.Offset(0, 12)),
        content=ft.Column(
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            spacing=2,
                            tight=True,
                            controls=[
                                ft.Text(
                                    profile.get("business_name") or "Nakitçe",
                                    color="#9ED9CB",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(sector_config["title"], color=WHITE, size=22, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                            border_radius=999,
                            bgcolor="#FFFFFF18",
                            content=ft.Text("Bugün", color="#D7F5EE", size=11, weight=ft.FontWeight.W_700),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=14,
                            border_radius=18,
                            bgcolor="#FFFFFF14",
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Kasada", color="#B7E8DC", size=12),
                                    ft.Text(
                                        money(records["cash_balance"]),
                                        color=WHITE,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=14,
                            border_radius=18,
                            bgcolor="#FFFFFF14",
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Alacağın", color="#FFE3A3", size=12),
                                    ft.Text(
                                        money(receivables),
                                        color=WHITE,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        primary_cta("Aldım", actions["income"], tone="teal"),
                        primary_cta("Verdim", actions["expense"], tone="red"),
                        primary_cta("Veresiye", actions["debt"], tone="amber"),
                    ],
                ),
                ft.Text(quota_line, color="#D7F5EE", size=11),
            ],
        ),
    )

    def due_label(customer):
        raw = customer.get("due_date") or ""
        try:
            due = date.fromisoformat(raw) if raw else None
        except ValueError:
            due = None
        if due is None:
            return "Vade yok"
        days = (due - today).days
        if days < 0:
            return f"{-days} gün gecikti"
        if days == 0:
            return "Vade bugün"
        if days == 1:
            return "Vade yarın"
        return f"{days} gün kaldı"

    queue = collection_queue(records, today, limit=3)
    call_rows = [
        card(
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=10,
                        height=42,
                        border_radius=8,
                        bgcolor=AMBER,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(customer["name"], color=INK, weight=ft.FontWeight.W_700, size=15),
                            ft.Text(
                                f"{money(customer['balance'])} · {due_label(customer)}",
                                color=MUTED,
                                size=12,
                            ),
                        ],
                    ),
                    ft.Button(
                        content="WhatsApp",
                        bgcolor="#25D366",
                        color=WHITE,
                        on_click=lambda e, picked=customer: actions["remind"](picked),
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                            shape=ft.RoundedRectangleBorder(radius=14),
                        ),
                    ),
                ],
            ),
            bgcolor=AMBER_SOFT,
            padding=14,
            radius=18,
        )
        for customer in queue
    ]
    call_section = ft.Column(
        spacing=10,
        controls=[
            section_label("Bugün ara"),
            *(
                call_rows
                or [
                    empty_state(
                        "Açık hesap yok",
                        "Veresiye yazınca en acil müşteriler burada belirir.",
                        button_label="Veresiye yaz",
                        on_click=actions["debt"],
                    )
                ]
            ),
        ],
    )

    totals = day_totals(records.get("transactions"), today)
    close_card = card(
        ft.Column(
            spacing=10,
            controls=[
                section_label("Akşam kapanışı"),
                ft.Row(
                    spacing=8,
                    controls=[
                        _mini_stat("Aldım", money(totals["income"]), TEAL, MINT),
                        _mini_stat("Verdim", money(totals["expense"]), RED, "#FFF0EF"),
                        _mini_stat("Tahsil", money(totals["collected"]), INK, "#EEF2F5"),
                    ],
                ),
            ],
        ),
        padding=14,
        radius=20,
    )

    recovered_amount = month_collected(records.get("transactions"), today)
    recovered_card = card(
        ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=16,
                    bgcolor=WHITE,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("₺", size=22, color=TEAL, weight=ft.FontWeight.BOLD),
                ),
                ft.Column(
                    expand=True,
                    spacing=2,
                    controls=[
                        ft.Text("Bu ay tahsil ettiğin", color=MUTED, size=12),
                        ft.Text(money(recovered_amount), color=INK, size=22, weight=ft.FontWeight.BOLD),
                    ],
                ),
            ],
        ),
        bgcolor=MINT,
        padding=16,
    )

    has_any_data = bool(
        records["transactions"]
        or records["customers"]
        or records["products"]
        or workspace.get("opening_set")
    )
    demo_banner = None
    if workspace.get("demo_mode"):
        demo_banner = card(
            ft.Row(
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text("Örnek işletme açık", color=INK, weight=ft.FontWeight.W_700, size=13),
                            ft.Text("Gerçek kayıt değil — istediğin zaman temizle.", color=MUTED, size=11),
                        ],
                    ),
                    ft.TextButton(content="Temizle", on_click=actions["clear_demo"]),
                ],
            ),
            bgcolor=MINT,
            padding=12,
            radius=16,
        )

    welcome = card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text("3 saniyede başla", color=INK, weight=ft.FontWeight.BOLD, size=18),
                ft.Text(
                    "Kasayı yaz veya ilk veresiyeyi gir. İstersen örnek bakkalla gez.",
                    color=MUTED,
                    size=13,
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        primary_cta("Aldım", actions["income"], tone="teal"),
                        primary_cta("Veresiye", actions["debt"], tone="amber"),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.TextButton(content="Kasadaki parayı yaz", on_click=actions["opening"]),
                        ft.TextButton(content="Örnekle dene", on_click=actions["load_demo"]),
                        ft.TextButton(content="Sesle / fişle", on_click=actions["intake"]),
                    ],
                ),
            ],
        ),
        bgcolor="#FFF9ED",
        padding=18,
        radius=22,
    )

    profile_nudge = None
    if not (profile.get("business_name") or "").strip() and has_any_data and not workspace.get("demo_mode"):
        profile_nudge = card(
            ft.Row(
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text("İşletme adı (isteğe bağlı)", color=INK, weight=ft.FontWeight.W_600, size=13),
                            ft.Text("Kısayollar iş koluna göre düzenlenir.", color=MUTED, size=11),
                        ],
                    ),
                    ft.TextButton(content="Tamamla", on_click=actions["edit_profile"]),
                ],
            ),
            bgcolor="#EAF2FF",
            padding=12,
            radius=16,
        )

    alert_section = None
    if alerts:
        alert_section = ft.Column(
            spacing=8,
            controls=[
                section_label("Kritik günler"),
                *[alert_card(item["title"], item["subtitle"], tone=item["tone"]) for item in alerts],
                ft.TextButton(content="+ Hatırlatma ekle", on_click=actions["add_reminder"]),
            ],
        )

    follow_bits = []
    if pending_pos:
        follow_bits.append(
            card(
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Text("POS bekleyen", color=INK, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Text(money(pending_pos), color="#A66A08", weight=ft.FontWeight.BOLD),
                    ],
                ),
                bgcolor="#FFF9ED",
                padding=14,
                radius=16,
            )
        )
    if low_stock:
        follow_bits.append(
            card(
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Text("Azalan stok", color=INK, weight=ft.FontWeight.W_600),
                        ft.Container(expand=True),
                        ft.Text(f"{low_stock} kalem", color=RED, weight=ft.FontWeight.BOLD),
                    ],
                ),
                bgcolor="#FFF0EF",
                padding=14,
                radius=16,
            )
        )

    recent = sorted(records["transactions"], key=lambda t: t.get("date", ""), reverse=True)[:4]
    recent_cards = []
    for item in recent:
        positive = item["type"] == "income"
        is_debt = item["type"] == "debt"
        tone = TEAL if positive else ("#A66A08" if is_debt else RED)
        recent_cards.append(
            card(
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(width=8, height=40, border_radius=8, bgcolor=tone),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(item["title"], color=INK, weight=ft.FontWeight.W_600, size=14),
                                ft.Text(
                                    f"{item['date']} · {'Aldım' if positive else ('Veresiye' if is_debt else 'Verdim')}",
                                    color=MUTED,
                                    size=12,
                                ),
                            ],
                        ),
                        ft.Text(
                            ("+" if positive else ("· " if is_debt else "−")) + money(item["amount"]),
                            color=tone,
                            weight=ft.FontWeight.BOLD,
                            size=14,
                        ),
                    ],
                ),
                padding=14,
                radius=18,
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
    chart_card = None
    if chart_total > 0:
        chart = ft.Image(
            src=pie_chart_data_uri(
                [(v, c) for v, c in ((chart_income, TEAL), (chart_expenses, RED)) if v > 0] or [(1, "#DCE5E3")],
                size=160,
            ),
            width=160,
            height=160,
            fit=ft.BoxFit.CONTAIN,
            semantics_label="Gelir ve gider pasta grafiği",
        )

        def _pct(value):
            return 0 if chart_total <= 0 else round(100 * value / chart_total)

        chart_card = card(
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    chart,
                    ft.Column(
                        expand=True,
                        spacing=10,
                        controls=[
                            ft.Text("Bu ayın dağılımı" if not is_premium else "Son 12 ay", color=INK, weight=ft.FontWeight.W_700),
                            ft.Text(f"Aldım %{_pct(chart_income)} · {money(chart_income)}", color=TEAL, size=13, weight=ft.FontWeight.W_600),
                            ft.Text(f"Verdim %{_pct(chart_expenses)} · {money(chart_expenses)}", color=RED, size=13, weight=ft.FontWeight.W_600),
                        ],
                    ),
                ],
            ),
            padding=14,
            radius=20,
        )

    more_row = ft.Row(
        wrap=True,
        spacing=8,
        controls=[
            ft.TextButton(content="Sesle / fişle", on_click=actions["intake"]),
            ft.TextButton(content="Hızlı satış", on_click=actions["sale"]),
            ft.TextButton(content="GİB e-Arşiv", on_click=actions["open_gib"]),
            *([ft.TextButton(content="Üyelik", on_click=actions["membership"])] if not is_premium else []),
        ],
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=14,
        controls=[
            hero,
            *([demo_banner] if demo_banner else []),
            *([] if has_any_data else [welcome]),
            *([profile_nudge] if profile_nudge else []),
            call_section,
            close_card,
            *([recovered_card] if recovered_amount > 0 else []),
            *([alert_section] if alert_section else []),
            *follow_bits,
            section_label("Bu ay"),
            ft.ResponsiveRow(
                controls=[
                    metric_tile("Aldım", money(income), "Gelen para", bgcolor="#EAF2FF", accent="#3565A8", col={"xs": 6, "md": 6}),
                    metric_tile("Verdim", money(expenses), "Giden para", bgcolor="#FFF0EF", accent=RED, col={"xs": 6, "md": 6}),
                ],
                spacing=10,
                run_spacing=10,
            ),
            *([chart_card] if chart_card else []),
            section_label("Son hareketler"),
            *(
                recent_cards
                or [
                    empty_state(
                        "Henüz hareket yok",
                        "İlk Aldım veya Verdim kaydını gir.",
                        button_label="Aldım",
                        on_click=actions["income"],
                        secondary_label="Verdim",
                        on_secondary=actions["expense"],
                    )
                ]
            ),
            more_row,
            ft.Text(
                f"Öneri: {SECTOR_REMINDER_HINTS.get(sector, 'İşletme kontrolü')}",
                color=MUTED,
                size=11,
            ),
            ft.TextButton(content="Gizlilik ve KVKK", on_click=actions["legal"]),
        ],
    )


def _mini_stat(label, value, color, bgcolor):
    return ft.Container(
        expand=True,
        padding=10,
        border_radius=14,
        bgcolor=bgcolor,
        content=ft.Column(
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(label, color=MUTED, size=11),
                ft.Text(value, color=color, size=13, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ],
        ),
    )
