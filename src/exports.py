import csv
import io
import unicodedata
from datetime import date

def _money(value):
    return f"₺{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
        writer.writerow([item.get("date", ""), "Gelen para" if item["type"] == "income" else ("Veresiye" if item["type"] == "debt" else "Giden para"), item["title"], f"{item['amount']:.2f}"])
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
        writer.writerow([item["bank"], f"{item['gross']:.2f}", item["rate"], f"{item['net']:.2f}", item["date"], "Geldi" if item["paid"] else "Bekliyor"])
    writer.writerow([])
    writer.writerow(["Teklifler", "Müşteri", "Malzeme (TL)", "İşçilik (TL)", "Toplam (TL)", "Tarih"])
    for quote in records["quotes"]:
        writer.writerow([quote["title"], quote["customer"], f"{quote['materials']:.2f}", f"{quote['labor']:.2f}", f"{quote['materials'] + quote['labor']:.2f}", quote["date"]])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def report_lines(records, profile=None):
    profile = profile or {}
    report_month = date.today().strftime("%Y-%m")
    monthly_transactions = [t for t in records["transactions"] if t.get("date", "").startswith(report_month)]
    monthly_income = sum(t["amount"] for t in monthly_transactions if t.get("type") == "income")
    monthly_expense = sum(t["amount"] for t in monthly_transactions if t.get("type") == "expense")
    lines = [
        "NAKITCE - ISLETME OZET RAPORU",
        "MALI MUSAVIR PAYLASIMI ICIN",
        "",
        f"Isletme: {profile.get('business_name', 'Isletme adi girilmedi')}",
        f"Yetkili: {profile.get('owner', '')}",
        f"Isletme turu: {profile.get('legal_form', '')} | Is kolu: {profile.get('sector', '')}",
        f"Vergi dairesi: {profile.get('tax_office', '')} | Vergi/T.C. no: {profile.get('tax_number', '')}",
        f"Adres: {profile.get('address', '')} | Telefon: {profile.get('phone', '')}",
        f"Rapor tarihi: {date.today().isoformat()} | Donem: {report_month}",
        "",
        f"Kasadaki para (uygulama kaydi): {_money(records['cash_balance'])}",
        f"Bu donem gelen para: {_money(monthly_income)}",
        f"Bu donem giden para: {_money(monthly_expense)}",
        f"Acik veresiye: {_money(sum(c.get('balance', 0) for c in records['customers']))}",
        "",
        "PARA HAREKETLERI",
    ]
    for item in sorted(monthly_transactions, key=lambda row: row.get("date", "")):
        kind = "Gelen" if item["type"] == "income" else ("Veresiye" if item["type"] == "debt" else "Giden")
        lines.append(f"{item.get('date', '')} | {kind} | {item['title']} | {_money(item['amount'])}")
    lines += ["", "VERESIYE BAKIYELERI"]
    for customer in records["customers"]:
        lines.append(f"{customer['name']} | {customer.get('phone', '')} | {_money(customer['balance'])}")
    lines += ["", "STOK OZETI"]
    for product in records["products"]:
        lines.append(f"{product['name']} | Barkod {product.get('barcode', '')} | Adet {product['qty']} | Uyari {product['min_qty']} | Fiyat {_money(product['price'])}")
    lines += ["", "POS HAREKETLERI"]
    for item in records["pos"]:
        lines.append(f"{item['date']} | {item['bank']} | Brut {_money(item['gross'])} | Net {_money(item['net'])} | {'Odendi' if item['paid'] else 'Bekliyor'}")
    lines += ["", "TEKLIFLER"]
    for quote in records["quotes"]:
        lines.append(f"{quote['date']} | {quote['customer']} | {quote['title']} | Toplam {_money(quote['materials'] + quote['labor'])}")
    lines += ["", "Bu yonetim ozeti bilgilendirme ve mali musavir paylasimi icindir; resmi defter veya beyanname degildir. Kayitlari mali musavirinizle dogrulayin."]
    return lines


def quote_lines(quote):
    total = quote["materials"] + quote["labor"]
    return [
        "NAKITCE - FIYAT TEKLIFI",
        "",
        f"Musteri: {quote['customer']}",
        f"Is: {quote['title']}",
        f"Tarih: {quote['date']}",
        "",
        f"Malzeme: {_money(quote['materials'])}",
        f"Iscilik: {_money(quote['labor'])}",
        f"Genel toplam: {_money(total)}",
        "",
        "Fiyat teklifi - resmi fatura degildir.",
    ]


def _ascii(text):
    replacements = str.maketrans({"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G", "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C", "₺": "TL"})
    normalized = unicodedata.normalize("NFKD", str(text).translate(replacements))
    return normalized.encode("ascii", "ignore").decode("ascii")


def pdf_bytes(lines):
    wrapped = []
    for line in lines:
        clean = _ascii(line)
        while len(clean) > 92:
            wrapped.append(clean[:92])
            clean = clean[92:]
        wrapped.append(clean)
    page_chunks = [wrapped[index:index + 52] for index in range(0, len(wrapped), 52)] or [[]]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids = []
    for chunk in page_chunks:
        page_id = len(objects) + 1
        content_id = page_id + 1
        page_ids.append(page_id)
        commands = ["BT", "/F1 10 Tf", "48 790 Td", "14 TL"]
        for line in chunk:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({safe}) Tj T*" if safe else "T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii")
        )
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode("ascii"))
        result.extend(obj)
        result.extend(b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    result.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode("ascii"))
    return bytes(result)
