import csv
import io
from datetime import date

from pdf_docs import business_report_pdf, customer_statement_pdf, quote_pdf


def _money(value):
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def money_tr(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def csv_report(records, profile=None):
    profile = profile or {}
    report_month = date.today().strftime("%Y-%m")
    monthly_transactions = [t for t in records["transactions"] if t.get("date", "").startswith(report_month)]
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["NAKİTÇE · İŞLETME ÖZET RAPORU"])
    writer.writerow(["İşletme", profile.get("business_name", "İşletme adı girilmedi")])
    writer.writerow(["Yetkili", profile.get("owner", "")])
    writer.writerow(["İşletme türü", profile.get("legal_form", "")])
    writer.writerow(["İş kolu", profile.get("sector", "")])
    writer.writerow(["Vergi dairesi", profile.get("tax_office", "")])
    writer.writerow(["Vergi / T.C. kimlik no", profile.get("tax_number", "")])
    writer.writerow(["Adres", profile.get("address", "")])
    writer.writerow(["Rapor tarihi", date.today().isoformat()])
    writer.writerow(["Rapor dönemi", report_month])
    writer.writerow([])
    writer.writerow(["Dönem özeti", "Tutar (TL)"])
    writer.writerow(["Gelen para", f"{sum(t['amount'] for t in monthly_transactions if t.get('type') == 'income'):.2f}"])
    writer.writerow(["Giden para", f"{sum(t['amount'] for t in monthly_transactions if t.get('type') == 'expense'):.2f}"])
    writer.writerow(["Açık veresiye (rapor tarihi itibarıyla)", f"{sum(c.get('balance', 0) for c in records['customers']):.2f}"])
    writer.writerow(["Kasa bakiyesi (uygulama kaydı)", f"{records.get('cash_balance', 0):.2f}"])
    writer.writerow([])
    writer.writerow(["Hareket tarihi", "Tür", "Açıklama", "Tutar (TL)"])
    for item in sorted(monthly_transactions, key=lambda row: row.get("date", "")):
        writer.writerow(
            [
                item.get("date", ""),
                "Gelen para" if item["type"] == "income" else ("Veresiye" if item["type"] == "debt" else "Giden para"),
                item["title"],
                f"{item['amount']:.2f}",
            ]
        )
    writer.writerow([])
    writer.writerow(["Müşterilerim", "Telefon", "Açık veresiye (TL)"])
    for customer in records["customers"]:
        writer.writerow([customer["name"], customer.get("phone", ""), f"{customer['balance']:.2f}"])
    writer.writerow([])
    writer.writerow(["Ürün ve hizmetler", "Barkod", "Stok", "Az stok uyarısı", "Birim fiyat (TL)"])
    for product in records["products"]:
        writer.writerow([product["name"], product.get("barcode", ""), product["qty"], product["min_qty"], f"{product['price']:.2f}"])
    writer.writerow([])
    writer.writerow(["POS", "Brüt (TL)", "Kesinti (%)", "Net (TL)", "Tahmini tarih", "Durum"])
    for item in records["pos"]:
        writer.writerow(
            [item["bank"], f"{item['gross']:.2f}", item["rate"], f"{item['net']:.2f}", item["date"], "Geldi" if item["paid"] else "Bekliyor"]
        )
    writer.writerow([])
    writer.writerow(["Teklifler", "Müşteri", "Malzeme (TL)", "İşçilik (TL)", "Toplam (TL)", "Tarih"])
    for quote in records["quotes"]:
        writer.writerow(
            [
                quote["title"],
                quote["customer"],
                f"{quote['materials']:.2f}",
                f"{quote['labor']:.2f}",
                f"{quote['materials'] + quote['labor']:.2f}",
                quote["date"],
            ]
        )
    return ("\ufeff" + output.getvalue()).encode("utf-8")


# Geriye dönük API: satır listeleri yerine doğrudan PDF baytı
def report_lines(records, profile=None):
    return business_report_pdf(records, profile)


def quote_lines(quote, profile=None):
    return quote_pdf(quote, profile)


def pdf_bytes(content):
    """Eski imza: satır listesi veya hazır PDF baytı kabul eder."""
    if isinstance(content, (bytes, bytearray)):
        return bytes(content)
    # Eski ASCII satır yolu artık kullanılmıyor; metni basit belgeye sar.
    from pdf_docs import NakitceDoc, _pdf_bytes

    doc = NakitceDoc("Belge")
    doc.add_page()
    for line in content:
        doc.body(str(line))
    return _pdf_bytes(doc)
