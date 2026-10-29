"""Yerel banka hesap hareketi CSV içe aktarma (açık bankacılık yok)."""

from __future__ import annotations

import csv
import io
import re
from datetime import date

from intake_text import _amount

_DATE_PATTERNS = [
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})$"),
    re.compile(r"^(\d{2})[./](\d{2})[./](\d{4})$"),
    re.compile(r"^(\d{2})[./](\d{2})[./](\d{2})$"),
]


def _parse_date(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    for pattern in _DATE_PATTERNS:
        match = pattern.match(value)
        if not match:
            continue
        parts = match.groups()
        if len(parts[0]) == 4:
            year, month, day = map(int, parts)
        elif len(parts[2]) == 4:
            day, month, year = map(int, parts)
        else:
            day, month, year = int(parts[0]), int(parts[1]), 2000 + int(parts[2])
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    return None


def _pick(row: dict, *names):
    lower_map = {str(key).casefold().strip(): value for key, value in row.items()}
    for name in names:
        if name.casefold() in lower_map:
            return lower_map[name.casefold()]
    for key, value in lower_map.items():
        for name in names:
            if name.casefold() in key:
                return value
    return ""


def parse_bank_csv(data: bytes) -> list[dict]:
    """CSV satırlarını gelir/gider adaylarına çevirir."""
    text = data.decode("utf-8-sig", errors="ignore")
    if ";" in text.splitlines()[0] and text.count(";") >= text.count(","):
        delimiter = ";"
    else:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for raw in reader:
        if not raw:
            continue
        tx_date = _parse_date(str(_pick(raw, "tarih", "date", "işlem tarihi", "islem tarihi", "valor")))
        description = str(_pick(raw, "açıklama", "aciklama", "description", "işlem", "islem", "narasyon") or "Banka hareketi").strip()
        amount_raw = _pick(raw, "tutar", "amount", "işlem tutarı", "islem tutari")
        credit = _pick(raw, "alacak", "credit", "yatırılan", "yatirilan")
        debit = _pick(raw, "borç", "borc", "debit", "çekilen", "cekilen")
        amount = None
        kind = "expense"
        if amount_raw not in ("", None):
            raw = str(amount_raw).replace("−", "-").strip()
            negative = raw.startswith("-") or raw.startswith("(")
            cleaned = raw.lstrip("-+").strip("() ")
            amount = _amount(cleaned)
            if amount is not None and negative:
                kind = "expense"
            elif amount is not None:
                lowered = description.casefold()
                kind = (
                    "expense"
                    if any(w in lowered for w in ("pos komisyon", "aidat", "ödeme", "odeme", "fatura", "alım", "alim"))
                    else "income"
                )
        else:
            credit_amount = _amount(str(credit)) if credit not in ("", None) else None
            debit_amount = _amount(str(debit)) if debit not in ("", None) else None
            if credit_amount:
                amount, kind = credit_amount, "income"
            elif debit_amount:
                amount, kind = debit_amount, "expense"
        if amount is None or amount <= 0:
            continue
        rows.append(
            {
                "date": tx_date or date.today().isoformat(),
                "type": kind,
                "title": f"Banka · {description}"[:120],
                "amount": amount,
            }
        )
    return rows
