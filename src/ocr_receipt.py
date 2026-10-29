"""Fiş / fatura metninden tutar, KDV ve satıcı çıkarımı; isteğe bağlı online OCR."""

from __future__ import annotations

import base64
import logging
import re
from io import BytesIO

import httpx
from pypdf import PdfReader

from intake_text import _amount, _PRIORITY_AMOUNT_PATTERN, _AMOUNT_PATTERN

log = logging.getLogger("app.ocr")

_SELLER_PATTERNS = [
    re.compile(r"(?:ünvan|unvan|satıcı|satici|firma|işyeri|isyeri)\s*[:：]?\s*(.+)", re.IGNORECASE),
    re.compile(r"^([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü0-9 .&'-]{3,60})\s*$", re.MULTILINE),
]
_KDV_PATTERN = re.compile(
    r"(?:kdv|katma\s*değer)\D{0,20}(%?\s*\d{1,2})?\D{0,16}"
    r"(\d{1,3}(?:[ .]\d{3})*(?:[,.]\d{1,2})?|\d+(?:[,.]\d{1,2})?)",
    re.IGNORECASE,
)
_VKN_PATTERN = re.compile(r"(?:vkn|vergi\s*no|vergi\s*kimlik)[^\d]{0,12}(\d{10,11})", re.IGNORECASE)


def parse_receipt_text(text: str, filename: str = "") -> dict:
    text = (text or "").strip()
    lowered = text.casefold()
    kind = "expense"
    if any(w in lowered for w in ("veresiye", "borç", "borc")):
        kind = "debt"
    elif any(w in lowered for w in ("tahsilat", "gelen para", "satış", "satis", "nakit giriş")):
        kind = "income"

    amount = None
    match = _PRIORITY_AMOUNT_PATTERN.search(text)
    if match:
        amount = _amount(match.group(1))
    if amount is None:
        found = _AMOUNT_PATTERN.search(text)
        amount = _amount(found.group(0)) if found else None

    kdv = None
    kdv_match = _KDV_PATTERN.search(text)
    if kdv_match:
        kdv = _amount(kdv_match.group(2))

    seller = ""
    for pattern in _SELLER_PATTERNS:
        seller_match = pattern.search(text)
        if seller_match:
            candidate = seller_match.group(1).strip()
            if len(candidate) >= 3 and "toplam" not in candidate.casefold():
                seller = candidate[:80]
                break

    vkn_match = _VKN_PATTERN.search(text)
    vkn = vkn_match.group(1) if vkn_match else ""

    title_parts = []
    if seller:
        title_parts.append(seller)
    elif filename:
        title_parts.append(filename.rsplit(".", 1)[0].replace("_", " ")[:40])
    else:
        title_parts.append("Fiş / fatura")
    if kdv is not None:
        title_parts.append(f"KDV {kdv:g}")

    return {
        "type": kind,
        "amount": amount,
        "kdv": kdv,
        "seller": seller,
        "vkn": vkn,
        "title": " · ".join(title_parts)[:120],
        "raw_preview": text[:400],
        "source": "text",
    }


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


async def ocr_image_bytes(data: bytes, filename: str = "fis.jpg") -> dict:
    """İnternet varsa OCR.space ücretsiz kotası ile okur; yoksa boş sonuç döner."""
    if not data:
        return parse_receipt_text("", filename)

    encoded = base64.b64encode(data).decode("ascii")
    payload = {
        "base64Image": f"data:image/jpeg;base64,{encoded}",
        "language": "tur",
        "isOverlayRequired": "false",
        "OCREngine": "2",
        "scale": "true",
    }
    headers = {"apikey": "helloworld"}
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://api.ocr.space/parse/image",
                data=payload,
                headers=headers,
            )
            response.raise_for_status()
            body = response.json()
    except Exception as error:
        log.info("OCR request failed: %s", error)
        return {
            **parse_receipt_text("", filename),
            "error": "OCR şu an kullanılamıyor. Tutarı elle gir veya metinli PDF dene.",
            "source": "ocr_failed",
        }

    if body.get("IsErroredOnProcessing"):
        message = body.get("ErrorMessage") or body.get("ErrorDetails") or "OCR hatası"
        if isinstance(message, list):
            message = "; ".join(str(item) for item in message)
        return {
            **parse_receipt_text("", filename),
            "error": str(message)[:160],
            "source": "ocr_failed",
        }

    parsed_results = body.get("ParsedResults") or []
    text = "\n".join(item.get("ParsedText") or "" for item in parsed_results).strip()
    result = parse_receipt_text(text, filename)
    result["source"] = "ocr"
    if not text:
        result["error"] = "Görselde okunabilir metin bulunamadı. Daha net çekip tekrar dene."
    return result


async def analyze_attachment(name: str, data: bytes, mime: str = "") -> dict:
    lower = (name or "").lower()
    mime = (mime or "").lower()
    if lower.endswith(".pdf") or "pdf" in mime:
        text = extract_pdf_text(data)
        result = parse_receipt_text(text, name)
        result["source"] = "pdf"
        if not text:
            result["error"] = "PDF'de seçilebilir metin yok. Fotoğraf OCR veya elle giriş dene."
        return result
    if any(lower.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp")) or mime.startswith("image/"):
        return await ocr_image_bytes(data, name)
    if lower.endswith((".txt", ".csv")) or mime.startswith("text/"):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="ignore")
        result = parse_receipt_text(text, name)
        result["source"] = "text"
        return result
    return parse_receipt_text("", name)
