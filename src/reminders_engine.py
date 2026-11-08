"""Esnaf dilinde kritik gün ve vade uyarıları üretir."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

# Resmî tarihler işletmeye göre değişir; metinler bilgilendirme amaçlıdır.
TAX_HINTS = [
    {
        "id": "kdv",
        "day": 26,
        "title": "KDV günü yaklaşıyor",
        "note": "Yarın/bugün KDV beyan veya ödeme penceresi olabilir. Kendi tebligatını kontrol et.",
        "lead_days": (1, 0),
    },
    {
        "id": "muhtasar",
        "day": 26,
        "title": "Muhtasar / stopaj kontrolü",
        "note": "Stopajlı ödemen varsa beyanname takvimini mali müşavirinle doğrula.",
        "lead_days": (2,),
    },
    {
        "id": "month_end",
        "day": 0,  # ayın son günü
        "title": "Ay sonu evrak kontrolü",
        "note": "Defter, fiş ve banka hareketlerini toparla. Beyan takvimini mali müşavirinle doğrula.",
        "lead_days": (3, 0),
    },
]


def _last_day(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def _tax_due_date(today: date, day: int) -> date:
    target_day = _last_day(today.year, today.month) if day <= 0 else min(day, _last_day(today.year, today.month))
    return date(today.year, today.month, target_day)


def critical_alerts(records, workspace, today=None) -> list[dict]:
    today = today or date.today()
    alerts = []

    for hint in TAX_HINTS:
        due = _tax_due_date(today, hint["day"])
        days_left = (due - today).days
        if days_left in hint["lead_days"] or (days_left == 1 and "Yarın" in hint["note"]):
            label = "Bugün" if days_left == 0 else ("Yarın" if days_left == 1 else f"{days_left} gün")
            title = hint["title"]
            if days_left == 1:
                title = title.replace("yaklaşıyor", "yarın")
            elif days_left == 0:
                title = title.replace("yaklaşıyor", "bugün")
            alerts.append(
                {
                    "kind": "tax",
                    "tone": "amber",
                    "title": title,
                    "subtitle": f"{label} · {hint['note']}",
                    "date": due.isoformat(),
                }
            )

    for customer in records.get("customers", []):
        balance = float(customer.get("balance") or 0)
        if balance <= 0:
            continue
        due_raw = customer.get("due_date") or ""
        try:
            due = date.fromisoformat(due_raw) if due_raw else None
        except ValueError:
            due = None
        if due is None:
            continue
        days_left = (due - today).days
        if days_left > 3:
            continue
        if days_left < 0:
            subtitle = f"{customer['name']} · {balance:,.0f} TL açık hesap gecikti"
            title = f"{customer['name'].split()[0]}'in borç vadesi geçti"
            tone = "red"
        elif days_left == 0:
            subtitle = f"{customer['name']} · {balance:,.0f} TL açık hesabın vadesi bugün"
            title = f"Komşunun / müşterinin borç vadesi geldi"
            tone = "amber"
        else:
            subtitle = f"{customer['name']} · {balance:,.0f} TL · {days_left} gün kaldı"
            title = f"{customer['name'].split()[0]}'in vadesi yaklaşıyor"
            tone = "amber"
        alerts.append(
            {
                "kind": "customer",
                "tone": tone,
                "title": title,
                "subtitle": subtitle.replace(",", "."),
                "date": due.isoformat(),
                "customer_id": customer.get("id"),
            }
        )

    for item in workspace.get("reminders", []):
        try:
            due = date.fromisoformat(item.get("date", ""))
        except ValueError:
            continue
        days_left = (due - today).days
        if days_left > 3 or days_left < -7:
            continue
        label = "Gecikti" if days_left < 0 else ("Bugün" if days_left == 0 else ("Yarın" if days_left == 1 else f"{days_left} gün"))
        alerts.append(
            {
                "kind": "reminder",
                "tone": "red" if days_left <= 0 else "teal",
                "title": item.get("title") or "Hatırlatma",
                "subtitle": f"{label} · {item.get('note') or item.get('date', '')}",
                "date": due.isoformat(),
            }
        )

    for pos in records.get("pos", []):
        if pos.get("paid"):
            continue
        try:
            due = date.fromisoformat(pos.get("date", ""))
        except ValueError:
            continue
        days_left = (due - today).days
        if days_left > 2:
            continue
        alerts.append(
            {
                "kind": "pos",
                "tone": "teal" if days_left >= 0 else "amber",
                "title": "POS'tan para gelecek" if days_left >= 0 else "POS tahsilatı gecikti mi?",
                "subtitle": f"{pos.get('bank', 'POS')} · net {pos.get('net', 0):,.2f} TL · {pos.get('date', '')}".replace(",", "X").replace(".", ",").replace("X", "."),
                "date": due.isoformat(),
            }
        )

    order = {"red": 0, "amber": 1, "teal": 2}
    alerts.sort(key=lambda row: (order.get(row["tone"], 9), row.get("date", "")))
    return alerts[:8]


def seed_tax_reminders(workspace, today=None) -> list[dict]:
    """Eksikse ayın KDV / ay sonu hatırlatmalarını ekler (yinelenmez)."""
    today = today or date.today()
    existing = {(item.get("title"), item.get("date")) for item in workspace.get("reminders", [])}
    added = []
    next_id = max((int(item.get("id", 0)) for item in workspace.get("reminders", [])), default=0)
    for hint in TAX_HINTS:
        due = _tax_due_date(today, hint["day"])
        if due < today:
            # bir sonraki aya taşı
            month = today.month + 1
            year = today.year + (1 if month > 12 else 0)
            month = 1 if month > 12 else month
            day = _last_day(year, month) if hint["day"] <= 0 else min(hint["day"], _last_day(year, month))
            due = date(year, month, day)
        key = (hint["title"], due.isoformat())
        if key in existing:
            continue
        next_id += 1
        item = {
            "id": next_id,
            "title": hint["title"],
            "date": due.isoformat(),
            "note": hint["note"],
            "sector": workspace.get("profile", {}).get("sector", ""),
            "auto": True,
        }
        workspace.setdefault("reminders", []).append(item)
        added.append(item)
    return added


def collection_queue(records, today=None, limit=3) -> list[dict]:
    """Borcu olan müşteriler: vadesi geçmiş önce, sonra en büyük bakiye."""
    today = today or date.today()
    ranked = []
    for customer in records.get("customers", []):
        balance = float(customer.get("balance") or 0)
        if balance <= 0:
            continue
        due_raw = customer.get("due_date") or ""
        try:
            due = date.fromisoformat(due_raw) if due_raw else None
        except ValueError:
            due = None
        days_left = (due - today).days if due else 10_000
        ranked.append((days_left, -balance, customer))
    ranked.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in ranked[:limit]]


def whatsapp_payment_received_message(customer, amount, profile=None) -> str:
    profile = profile or {}
    business = profile.get("business_name") or "işletmemiz"
    owner = (profile.get("owner") or "").strip()
    paid = f"{float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    left = f"{float(customer.get('balance') or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = owner or business
    return (
        f"Merhaba {customer['name']},\n\n"
        f"*{business}* olarak ödemenizi aldık.\n"
        f"Tahsil edilen: *{paid} TL*.\n"
        f"Kalan açık hesap: *{left} TL*.\n\n"
        f"Teşekkür ederiz.\n{sign}"
    )


def whatsapp_reminder_message(customer, profile=None) -> str:
    profile = profile or {}
    business = profile.get("business_name") or "işletmemiz"
    owner = (profile.get("owner") or "").strip()
    amount = f"{customer['balance']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    due = (customer.get("due_date") or "").strip()
    today = date.today().isoformat()
    if due == today:
        due_sentence = "Açık hesabınızın vadesi *bugün* gelmiştir."
    elif due:
        due_sentence = f"Açık hesabınızın vade tarihi: *{due}*."
    else:
        due_sentence = "Açık hesabınızı bilginize sunarız."
    sign = owner or business
    return (
        f"Merhaba {customer['name']},\n\n"
        f"*{business}* olarak nazik bir hatırlatma yapmak istedik.\n"
        f"Hesabınızdaki açık bakiye: *{amount} TL*.\n"
        f"{due_sentence}\n\n"
        f"Ödeme yaptıysanız bu mesajı dikkate almayınız. "
        f"Uygun bir zamanda haberleşmekten memnuniyet duyarız.\n\n"
        f"Ekstre PDF’ini bu sohbete ekledik.\n"
        f"Saygılarımızla,\n{sign}"
    )


def default_due_date(today=None, days=30) -> str:
    today = today or date.today()
    return (today + timedelta(days=days)).isoformat()
