"""Ücretsiz kasa ve WhatsApp kotası.

Veresiye bu kotaya girmez: borç defteri büyüyebilir.
Aldım, Verdim ve WhatsApp gönderimi ay başında sıfırlanır.
Premium bu tavanı kaldırır.
"""

from datetime import date

# Sakin bir dükkân günde iki kasa hareketiyle yaklaşık iki hafta gider.
# Sekiz WhatsApp, tahsilatı hissettirir; sonrası aboneliğin nedenidir.
FREE_CASH_OPS_MONTHLY = 30
FREE_WHATSAPP_MONTHLY = 8


def month_key(today=None) -> str:
    today = today or date.today()
    return today.strftime("%Y-%m")


def cash_ops_used(transactions, today=None) -> int:
    key = month_key(today)
    return sum(
        1
        for item in transactions or []
        if str(item.get("date", "")).startswith(key) and item.get("type") in {"income", "expense"}
    )


def whatsapp_used(workspace, today=None) -> int:
    usage = (workspace or {}).get("usage") or {}
    bucket = usage.get("whatsapp") or {}
    try:
        return max(0, int(bucket.get(month_key(today), 0)))
    except (TypeError, ValueError):
        return 0


def note_whatsapp_send(workspace, today=None) -> int:
    usage = workspace.setdefault("usage", {})
    bucket = usage.setdefault("whatsapp", {})
    key = month_key(today)
    bucket[key] = whatsapp_used(workspace, today) + 1
    return bucket[key]


def day_totals(transactions, today=None) -> dict:
    day = (today or date.today()).isoformat()
    income = expense = debt = collected = 0.0
    for item in transactions or []:
        if item.get("date") != day:
            continue
        amount = float(item.get("amount") or 0)
        kind = item.get("type")
        if kind == "income":
            income += amount
            if item.get("collection"):
                collected += amount
        elif kind == "expense":
            expense += amount
        elif kind == "debt":
            debt += amount
    return {"income": income, "expense": expense, "debt": debt, "collected": collected}


def month_collected(transactions, today=None) -> float:
    key = month_key(today)
    total = 0.0
    for item in transactions or []:
        if item.get("type") == "income" and item.get("collection") and str(item.get("date", "")).startswith(key):
            total += float(item.get("amount") or 0)
    return total
