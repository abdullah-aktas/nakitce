"""Görüntü baytlarından barkod / QR çözümü (pyzbar + Pillow)."""

from __future__ import annotations

import logging
from io import BytesIO

log = logging.getLogger("app.barcode")


def decode_barcode_bytes(data: bytes) -> str | None:
    if not data:
        return None
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
    except Exception as error:
        log.info("Barkod kütüphanesi yok: %s", error)
        return None

    try:
        image = Image.open(BytesIO(data))
    except Exception:
        # Ham frame (nadiren) — boyut bilinmiyorsa vazgeç
        return None

    if image.mode not in {"RGB", "L", "RGBA"}:
        image = image.convert("RGB")

    for candidate in (image, image.convert("L")):
        try:
            results = decode(candidate)
        except Exception as error:
            log.debug("decode failed: %s", error)
            results = []
        if results:
            raw = results[0].data
            text = raw.decode("utf-8", errors="ignore").strip() if isinstance(raw, (bytes, bytearray)) else str(raw).strip()
            if text:
                return text

    # Küçük / bulanık etiketler için büyütüp bir kez daha dene
    try:
        wide = image.resize((image.width * 2, image.height * 2))
        results = decode(wide.convert("L"))
        if results:
            raw = results[0].data
            text = raw.decode("utf-8", errors="ignore").strip() if isinstance(raw, (bytes, bytearray)) else str(raw).strip()
            return text or None
    except Exception:
        pass
    return None
