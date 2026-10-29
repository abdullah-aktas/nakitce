"""Quick smoke test for new Nakitçe features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bank_import import parse_bank_csv
from data import starter_data
from exports import customer_statement_pdf
from ocr_receipt import parse_receipt_text
from reminders_engine import critical_alerts, seed_tax_reminders, whatsapp_reminder_message
from voice_commands import parse_voice_command


def main():
    r = parse_voice_command("Ahmet Yilmaz'a 450 TL veresiye yaz")
    assert r["type"] == "debt" and r["amount"] == 450 and "Ahmet" in r["customer"], r
    r2 = parse_voice_command("Aldim 1250 gunluk satis")
    assert r2["type"] == "income" and r2["amount"] == 1250, r2
    text = parse_receipt_text("Yildiz Market\nToplam Tutar: 1.250,50 TL\nKDV %20 208,42")
    assert text["amount"] == 1250.5, text
    csv = (
        "Tarih;Aciklama;Tutar\n"
        "24.10.2026;POS Satis;1500,00\n"
        "23.10.2026;Mal alimi;-320,00\n"
    ).encode("utf-8")
    rows = parse_bank_csv(csv)
    assert len(rows) == 2, rows
    recs = starter_data()
    ws = {"profile": {"business_name": "Test Bakkal", "sector": "Bakkal / market"}, "reminders": []}
    alerts = critical_alerts(recs, ws)
    assert alerts, "expected critical alerts for due customers"
    seeded = seed_tax_reminders(ws)
    assert seeded
    pdf = customer_statement_pdf(recs["customers"][0], recs, ws["profile"])
    assert pdf.startswith(b"%PDF")
    msg = whatsapp_reminder_message(recs["customers"][0], ws["profile"])
    assert "Nakitçe hatırlatır" in msg
    print("smoke_ok", len(alerts), len(seeded), len(pdf))


if __name__ == "__main__":
    main()
