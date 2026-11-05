"""İlk açılış / mağaza demosu için örnek işletme verisi.

Gerçek kullanıcı verisinin üzerine yazılmaz; yalnızca açıkça istenince yüklenir.
"""

from datetime import date, timedelta


def showcase_workspace():
    today = date.today()
    return {
        "profile": {
            "business_name": "Miraş Bakkal",
            "owner": "Ayşe Yılmaz",
            "email": "",
            "sector": "Butik / perakende",
            "legal_form": "Şahıs",
            "tax_office": "",
            "tax_number": "",
            "phone": "05321234567",
            "address": "Kadıköy",
        },
        "mode": "simple",
        "reminders": [
            {
                "id": 1,
                "title": "Komşunun / müşterinin borç vadesi",
                "date": (today + timedelta(days=1)).isoformat(),
                "note": "Mehmet Kaya bakiyesini hatırlat.",
            }
        ],
        "opening_set": True,
        "demo_mode": True,
        "consent_v1": today.isoformat(),
    }


def showcase_records():
    """İsimler eski otomatik demodan farklı — storage.is_legacy_demo silmesin."""
    today = date.today()
    month = today.isoformat()[:7]
    d1 = today.isoformat()
    d2 = (today - timedelta(days=1)).isoformat()
    d3 = (today - timedelta(days=3)).isoformat()
    return {
        "customers": [
            {
                "id": 1,
                "name": "Mehmet Kaya",
                "phone": "905321112233",
                "balance": 450.0,
                "due_date": (today + timedelta(days=2)).isoformat(),
            },
            {
                "id": 2,
                "name": "Zeynep Aksoy",
                "phone": "905559998877",
                "balance": 0.0,
                "due_date": "",
            },
            {
                "id": 3,
                "name": "Güneş Sitesi",
                "phone": "902162223344",
                "balance": 1200.0,
                "due_date": (today + timedelta(days=5)).isoformat(),
            },
        ],
        "transactions": [
            {"id": 1, "type": "income", "title": "Günlük satış", "amount": 1850.0, "date": d1},
            {"id": 2, "type": "expense", "title": "Toptancı ödeme", "amount": 620.0, "date": d1},
            {"id": 3, "type": "debt", "title": "Mehmet Kaya veresiye", "amount": 450.0, "date": d2},
            {"id": 4, "type": "income", "title": "Nakit satış", "amount": 940.0, "date": d2},
            {"id": 5, "type": "expense", "title": "Kira / aidat", "amount": 3500.0, "date": f"{month}-01"},
            {"id": 6, "type": "income", "title": "Hafta sonu satış", "amount": 2100.0, "date": d3},
        ],
        "products": [
            {"id": 1, "name": "Ayçiçek yağı 2 L", "barcode": "8690123456789", "qty": 12, "min_qty": 5, "price": 185.0},
            {"id": 2, "name": "Çay 1 kg", "barcode": "8690987654321", "qty": 3, "min_qty": 4, "price": 249.0},
            {"id": 3, "name": "Su 0.5 L", "barcode": "", "qty": 48, "min_qty": 12, "price": 12.5},
        ],
        "pos": [
            {
                "id": 1,
                "bank": "Banka POS",
                "gross": 800.0,
                "rate": 2.49,
                "days": 3,
                "net": 780.08,
                "date": d2,
                "paid": False,
            }
        ],
        "quotes": [],
        "cash_balance": 4250.0,
        "notice": "Örnek veri — dene, sonra temizle.",
    }


def clear_demo_workspace(existing):
    """Örnek modu kapat; profil/onay kullanıcıya kalabilir."""
    workspace = dict(existing or {})
    workspace["demo_mode"] = False
    workspace.pop("opening_set", None)
    return workspace
