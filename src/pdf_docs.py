"""Profesyonel Türkçe PDF belgeleri (mesaj + tablo)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

FONT = Path(__file__).resolve().parent / "assets" / "fonts" / "DejaVuSans.ttf"
FONT_BOLD = FONT  # DejaVuSans tek dosya; kalın için aynı yüz (stil weight ile)

TEAL = (15, 155, 130)
INK = (14, 36, 51)
MUTED = (91, 115, 130)
LINE = (220, 230, 226)
HEADER_BG = (11, 28, 44)
WHITE = (255, 255, 255)
SOFT = (232, 247, 242)


def _money(value) -> str:
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def _kind_label(kind: str) -> str:
    return {"income": "Aldım", "expense": "Verdim", "debt": "Veresiye"}.get(kind, kind)


class NakitceDoc(FPDF):
    def __init__(self, title: str, business: str = ""):
        super().__init__(unit="mm", format="A4")
        self.doc_title = title
        self.business = business or "İşletme"
        self.set_auto_page_break(auto=True, margin=18)
        if not FONT.exists():
            raise FileNotFoundError(f"PDF fontu bulunamadı: {FONT}")
        self.add_font("Nakitce", "", str(FONT))
        self.add_font("Nakitce", "B", str(FONT))
        self.set_margins(16, 16, 16)

    def header(self):
        self.set_fill_color(*HEADER_BG)
        self.rect(0, 0, 210, 28, "F")
        self.set_xy(16, 8)
        self.set_text_color(*WHITE)
        self.set_font("Nakitce", "B", 16)
        self.cell(0, 8, "Nakitçe", ln=False)
        self.set_font("Nakitce", "", 10)
        self.set_xy(16, 16)
        self.cell(0, 6, "Ticaretin kalbi · esnafın cep defteri")
        self.set_xy(120, 10)
        self.set_font("Nakitce", "B", 11)
        self.cell(74, 6, self.doc_title, align="R")
        self.ln(22)
        self.set_text_color(*INK)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*LINE)
        self.line(16, self.get_y(), 194, self.get_y())
        self.set_y(-12)
        self.set_font("Nakitce", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8, f"Nakitçe ile hazırlandı · {date.today().isoformat()} · Sayfa {self.page_no()}/{{nb}}", align="C")

    def section_title(self, text: str):
        self.set_font("Nakitce", "B", 12)
        self.set_text_color(*TEAL)
        self.cell(0, 8, text, ln=True)
        self.set_text_color(*INK)

    def body(self, text: str, *, size=10):
        self.set_font("Nakitce", "", size)
        self.set_text_color(*INK)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def meta_block(self, rows: list[tuple[str, str]]):
        self.set_fill_color(*SOFT)
        self.set_draw_color(*LINE)
        y0 = self.get_y()
        self.rect(16, y0, 178, 6 + 6 * len(rows), "DF")
        self.set_xy(20, y0 + 2)
        for label, value in rows:
            self.set_font("Nakitce", "B", 9)
            self.set_text_color(*MUTED)
            self.cell(42, 6, label)
            self.set_font("Nakitce", "", 9)
            self.set_text_color(*INK)
            self.cell(0, 6, value or "—", ln=True)
            self.set_x(20)
        self.set_y(y0 + 8 + 6 * len(rows))

    def table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None):
        if not col_widths:
            usable = 178
            col_widths = [usable / len(headers)] * len(headers)
        self.set_font("Nakitce", "B", 9)
        self.set_fill_color(*TEAL)
        self.set_text_color(*WHITE)
        for width, header in zip(col_widths, headers):
            self.cell(width, 7, header, border=0, fill=True)
        self.ln()
        self.set_text_color(*INK)
        self.set_font("Nakitce", "", 8.5)
        fill = False
        for row in rows:
            if self.get_y() > 270:
                self.add_page()
                self.set_font("Nakitce", "B", 9)
                self.set_fill_color(*TEAL)
                self.set_text_color(*WHITE)
                for width, header in zip(col_widths, headers):
                    self.cell(width, 7, header, border=0, fill=True)
                self.ln()
                self.set_text_color(*INK)
                self.set_font("Nakitce", "", 8.5)
            self.set_fill_color(248, 251, 250) if fill else self.set_fill_color(*WHITE)
            heights = []
            for width, cell in zip(col_widths, row):
                heights.append(self.get_string_width(str(cell)) / max(width - 1, 1))
            # single-line cells for clarity
            for width, cell in zip(col_widths, row):
                self.cell(width, 6.5, str(cell)[:48], border=0, fill=True)
            self.ln()
            fill = not fill
        self.ln(3)

    def highlight_box(self, title: str, value: str):
        self.set_fill_color(*SOFT)
        self.set_draw_color(*TEAL)
        y = self.get_y()
        self.rect(16, y, 178, 18, "DF")
        self.set_xy(20, y + 3)
        self.set_font("Nakitce", "", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 5, title, ln=True)
        self.set_x(20)
        self.set_font("Nakitce", "B", 14)
        self.set_text_color(*INK)
        self.cell(0, 8, value, ln=True)
        self.set_y(y + 22)


def _pdf_bytes(doc: NakitceDoc) -> bytes:
    doc.alias_nb_pages()
    return bytes(doc.output())


def customer_statement_pdf(customer, records, profile=None) -> bytes:
    profile = profile or {}
    business = profile.get("business_name") or "İşletme"
    owner = profile.get("owner") or ""
    phone = profile.get("phone") or ""
    name = customer.get("name", "Müşteri")
    balance = float(customer.get("balance") or 0)
    due = customer.get("due_date") or "Belirtilmedi"
    related = [
        item
        for item in records.get("transactions", [])
        if name.casefold() in str(item.get("title", "")).casefold()
        or item.get("customer_id") == customer.get("id")
    ]
    related = sorted(related, key=lambda row: row.get("date", ""))[-30:]

    doc = NakitceDoc("Hesap ekstresi", business)
    doc.add_page()
    doc.section_title("Sayın müşterimize")
    greeting = (
        f"Sayın {name},\n\n"
        f"{business} olarak hesabınızdaki açık bakiyeyi bilginize sunarız. "
        f"Bu belge bilgilendirme amaçlıdır; resmi fatura veya icra belgesi değildir. "
        f"Ödemeleriniz için teşekkür eder, kolaylıklar dileriz."
    )
    if owner:
        greeting += f"\n\nSaygılarımızla,\n{owner}\n{business}"
    else:
        greeting += f"\n\nSaygılarımızla,\n{business}"
    doc.body(greeting)

    doc.meta_block(
        [
            ("İşletme", business),
            ("İşletme telefonu", phone),
            ("Müşteri", name),
            ("Müşteri telefon", customer.get("phone") or "—"),
            ("Düzenleme", date.today().isoformat()),
            ("Vade", due),
        ]
    )
    doc.highlight_box("Güncel açık bakiye", _money(balance))

    doc.section_title("Hareket özeti")
    rows = []
    for item in related:
        rows.append(
            [
                item.get("date", ""),
                _kind_label(item.get("type", "")),
                str(item.get("title", ""))[:40],
                _money(item.get("amount", 0)),
            ]
        )
    if not rows:
        doc.body("Bu müşteriye bağlı hareket kaydı bulunamadı.")
    else:
        doc.table(
            ["Tarih", "Tür", "Açıklama", "Tutar"],
            rows,
            col_widths=[28, 28, 82, 40],
        )
    doc.body(
        "Not: Ödeme yaptıysanız bu mesajı dikkate almayınız. "
        "Sorularınız için lütfen işletmemizle iletişime geçiniz.",
        size=9,
    )
    return _pdf_bytes(doc)


def business_report_pdf(records, profile=None) -> bytes:
    profile = profile or {}
    business = profile.get("business_name") or "İşletme"
    report_month = date.today().strftime("%Y-%m")
    monthly = [t for t in records.get("transactions", []) if str(t.get("date", "")).startswith(report_month)]
    income = sum(t["amount"] for t in monthly if t.get("type") == "income")
    expense = sum(t["amount"] for t in monthly if t.get("type") == "expense")
    receivables = sum(c.get("balance", 0) for c in records.get("customers", []))

    doc = NakitceDoc("İşletme özet raporu", business)
    doc.add_page()
    doc.section_title("Mali müşavir paylaşımı için özet")
    doc.body(
        "Bu rapor Nakitçe uygulama kayıtlarından üretilmiştir. "
        "Resmi defter veya beyanname yerine geçmez; kayıtları mali müşavirinizle doğrulayınız."
    )
    doc.meta_block(
        [
            ("İşletme", business),
            ("Yetkili", profile.get("owner") or "—"),
            ("Tür / kol", f"{profile.get('legal_form', '')} / {profile.get('sector', '')}".strip(" /")),
            ("Vergi dairesi", profile.get("tax_office") or "—"),
            ("VKN / TCKN", profile.get("tax_number") or "—"),
            ("Adres", profile.get("address") or "—"),
            ("Dönem", report_month),
            ("Rapor tarihi", date.today().isoformat()),
        ]
    )
    doc.highlight_box("Kasa bakiyesi (uygulama)", _money(records.get("cash_balance", 0)))
    doc.table(
        ["Kalem", "Tutar"],
        [
            ["Bu dönem aldım (gelen)", _money(income)],
            ["Bu dönem verdim (giden)", _money(expense)],
            ["Açık veresiye", _money(receivables)],
        ],
        col_widths=[118, 60],
    )

    doc.section_title("Para hareketleri")
    tx_rows = [
        [
            item.get("date", ""),
            _kind_label(item.get("type", "")),
            str(item.get("title", ""))[:42],
            _money(item.get("amount", 0)),
        ]
        for item in sorted(monthly, key=lambda row: row.get("date", ""))
    ]
    if tx_rows:
        doc.table(["Tarih", "Tür", "Açıklama", "Tutar"], tx_rows, [28, 28, 82, 40])
    else:
        doc.body("Bu dönemde hareket yok.")

    doc.section_title("Veresiye bakiyeleri")
    cust_rows = [
        [c.get("name", ""), c.get("phone", "") or "—", c.get("due_date", "") or "—", _money(c.get("balance", 0))]
        for c in records.get("customers", [])
    ]
    if cust_rows:
        doc.table(["Müşteri", "Telefon", "Vade", "Bakiye"], cust_rows, [55, 45, 35, 43])

    doc.section_title("Stok özeti")
    prod_rows = [
        [
            p.get("name", ""),
            str(p.get("barcode", "") or "—"),
            str(p.get("qty", "")),
            _money(p.get("price", 0)),
        ]
        for p in records.get("products", [])
    ]
    if prod_rows:
        doc.table(["Ürün / hizmet", "Barkod", "Stok", "Fiyat"], prod_rows, [70, 48, 25, 35])

    if records.get("pos"):
        doc.section_title("POS tahsilatları")
        pos_rows = [
            [
                item.get("date", ""),
                item.get("bank", ""),
                _money(item.get("gross", 0)),
                _money(item.get("net", 0)),
                "Geldi" if item.get("paid") else "Bekliyor",
            ]
            for item in records["pos"]
        ]
        doc.table(["Tarih", "Banka", "Brüt", "Net", "Durum"], pos_rows, [28, 45, 35, 35, 35])

    if records.get("quotes"):
        doc.section_title("Teklifler")
        q_rows = [
            [
                q.get("date", ""),
                q.get("customer", ""),
                str(q.get("title", ""))[:36],
                _money(q.get("materials", 0) + q.get("labor", 0)),
            ]
            for q in records["quotes"]
        ]
        doc.table(["Tarih", "Müşteri", "İş", "Toplam"], q_rows, [28, 45, 70, 35])

    return _pdf_bytes(doc)


def quote_pdf(quote, profile=None) -> bytes:
    profile = profile or {}
    business = profile.get("business_name") or "İşletme"
    total = float(quote.get("materials", 0)) + float(quote.get("labor", 0))
    doc = NakitceDoc("Fiyat teklifi", business)
    doc.add_page()
    doc.section_title("Sayın müşterimize")
    doc.body(
        f"Sayın {quote.get('customer', '')},\n\n"
        f"Aşağıda \"{quote.get('title', '')}\" işi için hazırladığımız fiyat teklifini bilginize sunarız. "
        f"Bu teklif resmi fatura değildir; onayınız sonrası faturalandırma ayrıca yapılır."
    )
    doc.meta_block(
        [
            ("İşletme", business),
            ("Telefon", profile.get("phone") or "—"),
            ("Müşteri", quote.get("customer", "")),
            ("İş", quote.get("title", "")),
            ("Tarih", quote.get("date", date.today().isoformat())),
        ]
    )
    doc.table(
        ["Kalem", "Tutar"],
        [
            ["Malzeme", _money(quote.get("materials", 0))],
            ["İşçilik", _money(quote.get("labor", 0))],
            ["Genel toplam", _money(total)],
        ],
        col_widths=[118, 60],
    )
    doc.body("Teklif geçerliliği ve kapsam için lütfen bizimle görüşünüz. İlginize teşekkür ederiz.")
    return _pdf_bytes(doc)
