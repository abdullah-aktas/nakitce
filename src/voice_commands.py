"""Türkçe ses/dikte komutlarını hareket kaydına çevirir."""

from __future__ import annotations

import re

from intake_text import _amount, _AMOUNT_PATTERN

_VERESIYE = re.compile(
    r"(?P<name>.+?)(?:['’]?(?:a|e|ya|ye))?\s+"
    r"(?P<amount>\d[\d.,]*)\s*(?:tl|₺|lira)?\s*"
    r"(?:veresiye|borç|borc|açık\s*hesap)",
    re.IGNORECASE,
)
_VERESIYE_ALT = re.compile(
    r"(?:veresiye|borç|borc)\s+(?:yaz|ekle|kaydet)?\s*"
    r"(?P<name>.+?)\s+(?P<amount>\d[\d.,]*)\s*(?:tl|₺|lira)?",
    re.IGNORECASE,
)
_ALDIM = re.compile(
    r"(?:aldım|aldim|gelen\s*para|para\s*geldi|tahsilat|sattım|sattim)\s*"
    r"(?P<amount>\d[\d.,]*)?\s*(?:tl|₺|lira)?\s*(?P<title>.*)",
    re.IGNORECASE,
)
_VERDIM = re.compile(
    r"(?:verdim|giden\s*para|para\s*çıktı|para\s*cikti|harcadım|harcadim|masraf|gider)\s*"
    r"(?P<amount>\d[\d.,]*)?\s*(?:tl|₺|lira)?\s*(?P<title>.*)",
    re.IGNORECASE,
)
_AMOUNT_FIRST = re.compile(
    r"(?P<amount>\d[\d.,]*)\s*(?:tl|₺|lira)\s+"
    r"(?P<rest>.+)",
    re.IGNORECASE,
)


def parse_voice_command(text: str) -> dict:
    """Dönen alanlar: type, amount, title, customer, confidence, summary."""
    raw = (text or "").strip()
    if not raw:
        return {
            "type": "income",
            "amount": None,
            "title": "",
            "customer": "",
            "confidence": 0.0,
            "summary": "",
        }

    lowered = raw.casefold()
    for pattern in (_VERESIYE, _VERESIYE_ALT):
        match = pattern.search(raw)
        if match:
            name = re.sub(r"\s+", " ", match.group("name")).strip(" .,")
            name = re.sub(r"^(?:müşteri|musteri)\s+", "", name, flags=re.IGNORECASE)
            amount = _amount(match.group("amount"))
            return {
                "type": "debt",
                "amount": amount,
                "title": "Veresiye",
                "customer": name,
                "confidence": 0.92 if amount and name else 0.6,
                "summary": f"Veresiye · {name}" + (f" · {amount} TL" if amount else ""),
            }

    if any(w in lowered for w in ("veresiye", "borç yaz", "borc yaz", "açık hesap")):
        amount_match = _AMOUNT_PATTERN.search(raw)
        amount = _amount(amount_match.group(0)) if amount_match else None
        name = re.sub(
            r"(veresiye|borç|borc|açık\s*hesap|yaz|ekle|tl|₺|lira|\d[\d.,]*)",
            " ",
            raw,
            flags=re.IGNORECASE,
        )
        name = re.sub(r"\s+", " ", name).strip(" .,")
        return {
            "type": "debt",
            "amount": amount,
            "title": "Veresiye",
            "customer": name,
            "confidence": 0.7 if name else 0.45,
            "summary": f"Veresiye · {name or '?'}" + (f" · {amount} TL" if amount else ""),
        }

    for kind, pattern, default_title in (
        ("income", _ALDIM, "Gelen para"),
        ("expense", _VERDIM, "Giden para"),
    ):
        match = pattern.search(raw)
        if match:
            amount_token = match.groupdict().get("amount") or ""
            amount = _amount(amount_token) if amount_token else None
            if amount is None:
                found = _AMOUNT_PATTERN.search(raw)
                amount = _amount(found.group(0)) if found else None
            title = (match.groupdict().get("title") or "").strip(" .,")
            title = re.sub(r"^(?:tl|₺|lira)\s*", "", title, flags=re.IGNORECASE).strip()
            return {
                "type": kind,
                "amount": amount,
                "title": title or default_title,
                "customer": "",
                "confidence": 0.85 if amount else 0.55,
                "summary": f"{'Aldım' if kind == 'income' else 'Verdim'}"
                + (f" · {amount} TL" if amount else "")
                + (f" · {title}" if title else ""),
            }

    amount_first = _AMOUNT_FIRST.search(raw)
    if amount_first:
        amount = _amount(amount_first.group("amount"))
        rest = amount_first.group("rest").strip()
        kind = "expense" if any(w in rest.casefold() for w in ("gider", "masraf", "alım", "alim", "ödeme", "odeme")) else "income"
        return {
            "type": kind,
            "amount": amount,
            "title": rest or ("Gelen para" if kind == "income" else "Giden para"),
            "customer": "",
            "confidence": 0.65,
            "summary": rest,
        }

    found = _AMOUNT_PATTERN.search(raw)
    amount = _amount(found.group(0)) if found else None
    kind = "income"
    if any(w in lowered for w in ("gider", "giden", "masraf", "harcama", "verdim", "ödeme", "odeme")):
        kind = "expense"
    return {
        "type": kind,
        "amount": amount,
        "title": raw[:120],
        "customer": "",
        "confidence": 0.35 if amount else 0.15,
        "summary": raw[:80],
    }
