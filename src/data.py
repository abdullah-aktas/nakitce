from copy import deepcopy


def starter_data():
    return deepcopy(
        {
            "customers": [
                {"id": 1, "name": "Ahmet Yılmaz", "phone": "905321234567", "balance": 1450.0},
                {"id": 2, "name": "Deniz Apartmanı", "phone": "905551112233", "balance": 620.0},
                {"id": 3, "name": "Elif Demir", "phone": "905301234567", "balance": 0.0},
            ],
            "transactions": [
                {"id": 1, "type": "income", "title": "Günlük satış", "amount": 3280.0, "date": "2026-10-21"},
                {"id": 2, "type": "expense", "title": "Mal alımı · Yıldız Toptan", "amount": 1160.0, "date": "2026-10-21"},
                {"id": 3, "type": "income", "title": "Servis ücreti", "amount": 850.0, "date": "2026-10-20"},
            ],
            "products": [
                {"id": 1, "name": "Filtre kahve 250 g", "barcode": "8691000000012", "qty": 7, "min_qty": 5, "price": 185.0},
                {"id": 2, "name": "Uzatma kablosu 5 m", "barcode": "8691000000029", "qty": 3, "min_qty": 4, "price": 240.0},
                {"id": 3, "name": "Montaj işçiligi", "barcode": "", "qty": 99, "min_qty": 0, "price": 650.0},
            ],
            "pos": [
                {"id": 1, "bank": "Banka POS", "gross": 2400.0, "rate": 2.49, "days": 3, "date": "2026-10-23", "net": 2340.24, "paid": False},
            ],
            "quotes": [
                {"id": 1, "customer": "Deniz Apartmanı", "title": "Banyo batarya değişimi", "materials": 1850.0, "labor": 1200.0, "date": "2026-10-21"},
            ],
            "cash_balance": 12650.0,
            "notice": "Kayıtlar bu cihazda saklanır. Bulut eşitlemesi henüz bağlanmadı.",
        }
    )
