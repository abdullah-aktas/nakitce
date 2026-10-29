def starter_data():
    """Yeni kurulum: hiç örnek veri yok, kayıtlar kullanıcı girdikçe oluşur."""
    return {
        "customers": [],
        "transactions": [],
        "products": [],
        "pos": [],
        "quotes": [],
        "cash_balance": 0.0,
        "notice": "",
    }


_DEMO_CUSTOMERS = {"Ahmet Yılmaz", "Deniz Apartmanı", "Elif Demir"}


def is_legacy_demo(records):
    """Eski sürümün otomatik yazdığı örnek veriyi tanır (kullanıcı verisi değildir)."""
    try:
        names = {c.get("name") for c in records.get("customers", [])}
        products = {p.get("name") for p in records.get("products", [])}
        return (
            len(records.get("customers", [])) == 3
            and names == _DEMO_CUSTOMERS
            and "Filtre kahve 250 g" in products
            and "Uzatma kablosu 5 m" in products
        )
    except (AttributeError, TypeError, ValueError):
        return False
