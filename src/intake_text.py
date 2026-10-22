import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


_AMOUNT_PATTERN = re.compile(r"(?<!\d)(?:\d{1,3}(?:[ .]\d{3})+|\d+)(?:[,.]\d{1,2})?(?!\d)")
_PRIORITY_AMOUNT_PATTERN = re.compile(
    r"(?:genel\s+toplam|ödenecek|toplam\s+tutar|toplam|tahsilat|tutar)\D{0,24}"
    r"(\d{1,3}(?:[ .]\d{3})*(?:[,.]\d{1,2})?|\d+(?:[,.]\d{1,2})?)",
    re.IGNORECASE,
)


def _amount(token):
    token = token.replace(" ", "")
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(".", "").replace(",", ".")
    elif "." in token and len(token.rsplit(".", 1)[1]) == 3:
        token = token.replace(".", "")
    try:
        value = float(token)
        return round(value, 2) if value > 0 else None
    except ValueError:
        return None


def parse_intake_text(text, filename=""):
    text = (text or "").strip()
    lowered = text.casefold()
    kind = "income"
    if any(word in lowered for word in ("veresiye", "borç", "borc", "açık hesap")):
        kind = "debt"
    elif any(word in lowered for word in ("gider", "giden para", "harcama", "masraf", "mal alımı", "ödeme", "odeme", "aldım", "aldim")):
        kind = "expense"

    match = _PRIORITY_AMOUNT_PATTERN.search(text)
    if match:
        amount_token = match.group(1)
    else:
        match = _AMOUNT_PATTERN.search(text)
        amount_token = match.group(0) if match else ""
    title = text
    if not title and filename:
        title = Path(filename).stem.replace("_", " ").replace("-", " ")
    return {"type": kind, "amount": _amount(amount_token) if amount_token else None, "title": title}


def extract_pdf_text(data):
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
