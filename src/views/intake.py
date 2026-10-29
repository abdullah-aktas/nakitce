import base64
from datetime import datetime
from pathlib import Path

import flet as ft
from flet_camera import Camera, CameraLensDirection, ResolutionPreset

from ocr_receipt import analyze_attachment
from voice_commands import parse_voice_command
from views.common import AMBER_SOFT, GOLD, INK, MINT, MUTED, RED, RED_SOFT, TEAL, WHITE, big_choice


MAX_FILE_BYTES = 1_500_000
MAX_EVIDENCE_BYTES = 3_000_000
ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp", "txt", "csv"]


def show(page, file_picker, submit, saved_evidence, initial_type="income"):
    selected_type = {"value": initial_type if initial_type in {"income", "expense", "debt"} else "income"}
    attachments = []
    camera = Camera(width=340, height=220, visible=False)
    camera_ready = {"value": False}
    existing_size = sum(
        len(base64.b64decode(item.get("data", "")))
        for items in saved_evidence.values()
        for item in items
    )

    voice_text = ft.TextField(
        label="Sesle veya yazarak anlat",
        hint_text="Örn. Ahmet Yılmaz'a 450 TL veresiye yaz",
        multiline=True,
        min_lines=2,
        max_lines=4,
        border_radius=16,
        filled=True,
        bgcolor=WHITE,
    )
    amount = ft.TextField(label="Tutar (TL)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=16, filled=True, bgcolor=WHITE)
    title = ft.TextField(label="Açıklama", border_radius=16, filled=True, bgcolor=WHITE)
    customer = ft.TextField(label="Müşteri adı · veresiye", visible=selected_type["value"] == "debt", border_radius=16, filled=True, bgcolor=WHITE)
    due_date = ft.TextField(
        label="Vade (YYYY-AA-GG)",
        hint_text="Boş bırakırsan 30 gün sonrası",
        visible=selected_type["value"] == "debt",
        border_radius=16,
        filled=True,
        bgcolor=WHITE,
    )
    notice = ft.Text("Yeşil = Aldım, kırmızı = Verdim. Mikrofon için yazı alanına dokun.", color=MUTED, size=12)
    evidence_label = ft.Text("Fiş eklenmedi.", color=MUTED, size=12)
    summary = ft.Text("", color=TEAL, size=13, weight=ft.FontWeight.W_600)
    type_chips = {}

    def refresh_type_ui():
        for kind, wrapper in type_chips.items():
            selected = selected_type["value"] == kind
            if kind == "income":
                wrapper.bgcolor = TEAL if selected else MINT
                wrapper.content.color = WHITE if selected else TEAL
            elif kind == "expense":
                wrapper.bgcolor = RED if selected else RED_SOFT
                wrapper.content.color = WHITE if selected else RED
            else:
                wrapper.bgcolor = GOLD if selected else AMBER_SOFT
                wrapper.content.color = INK  # sarı zeminde beyaz okunmaz
        customer.visible = selected_type["value"] == "debt"
        due_date.visible = selected_type["value"] == "debt"
        page.update()

    def select_type(kind):
        selected_type["value"] = kind
        refresh_type_ui()

    type_row = ft.Row(spacing=8, wrap=True)
    for kind, label in (("income", "Aldım"), ("expense", "Verdim"), ("debt", "Veresiye")):
        wrapper = ft.Container(
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            border_radius=999,
            bgcolor=TEAL if kind == "income" else (RED_SOFT if kind == "expense" else AMBER_SOFT),
            on_click=lambda e, k=kind: select_type(k),
            ink=True,
            content=ft.Text(
                label,
                weight=ft.FontWeight.BOLD,
                color=WHITE if kind == "income" else (RED if kind == "expense" else INK),
            ),
        )
        type_chips[kind] = wrapper
        type_row.controls.append(wrapper)
    refresh_type_ui()

    def refresh_evidence_label():
        if attachments:
            names = " · ".join(item["name"] for item in attachments)
            evidence_label.value = f"Eklenenler ({len(attachments)}): {names}"
        else:
            evidence_label.value = "Fiş eklenmedi."
        page.update()

    def current_attachment_bytes():
        return sum(len(item["bytes"]) for item in attachments)

    def add_attachment(name, data, mime):
        size = len(data or b"")
        if not size:
            notice.value = "Dosya içeriği okunamadı."
            page.update()
            return False
        if size > MAX_FILE_BYTES:
            notice.value = "Her dosya en fazla 1,5 MB olabilir."
            page.update()
            return False
        if existing_size + current_attachment_bytes() + size > MAX_EVIDENCE_BYTES:
            notice.value = "Belge alanı doldu (3 MB). Eski ekleri temizle."
            page.update()
            return False
        attachments.append({"name": name, "mime": mime, "bytes": data})
        refresh_evidence_label()
        return True

    def apply_parsed(parsed):
        if parsed.get("type") in {"income", "expense", "debt"}:
            selected_type["value"] = parsed["type"]
        if parsed.get("amount") is not None:
            amount.value = str(parsed["amount"]).replace(".", ",")
        if parsed.get("title"):
            title.value = str(parsed["title"])[:120]
        if parsed.get("customer"):
            customer.value = parsed["customer"]
        summary.value = parsed.get("summary") or parsed.get("title") or ""
        refresh_type_ui()

    def on_voice_text_change(e):
        parsed = parse_voice_command(e.control.value)
        apply_parsed(parsed)
        conf = parsed.get("confidence", 0)
        notice.value = (
            f"Anladım (%{int(conf * 100)}): {parsed.get('summary') or '—'}. Kaydetmeden önce kontrol et."
            if conf >= 0.45
            else "Komutu netleştir: örn. “Ahmet'e 450 TL veresiye yaz” veya “Aldım 1250 günlük satış”."
        )
        page.update()

    voice_text.on_change = on_voice_text_change

    async def open_camera():
        camera.visible = True
        notice.value = "Kamera açılıyor…"
        page.update()
        try:
            cameras = await camera.get_available_cameras()
            if not cameras:
                raise RuntimeError("Kamera yok.")
            description = next(
                (item for item in cameras if item.lens_direction == CameraLensDirection.BACK),
                cameras[0],
            )
            await camera.initialize(
                description=description,
                resolution_preset=ResolutionPreset.MEDIUM,
                enable_audio=False,
            )
            camera_ready["value"] = True
            capture_button.disabled = False
            notice.value = "Fişi kadraja al, çek — tutar ve KDV otomatik okunur."
        except Exception as error:
            camera.visible = False
            notice.value = f"Kamera açılamadı. Belge yükle. ({str(error)[:90]})"
        page.update()

    async def capture_photo():
        if not camera_ready["value"]:
            return
        try:
            data = await camera.take_picture()
            name = f"fis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            if add_attachment(name, data, "image/jpeg"):
                camera.visible = False
                await camera.pause_preview()
                camera_ready["value"] = False
                capture_button.disabled = True
                notice.value = "Fotoğraf eklendi, okunuyor…"
                page.update()
                result = await analyze_attachment(name, data, "image/jpeg")
                apply_parsed(
                    {
                        "type": result.get("type", "expense"),
                        "amount": result.get("amount"),
                        "title": result.get("title"),
                        "customer": "",
                        "summary": result.get("title"),
                        "confidence": 0.8 if result.get("amount") else 0.4,
                    }
                )
                if result.get("error"):
                    notice.value = result["error"]
                else:
                    kdv = result.get("kdv")
                    seller = result.get("seller") or ""
                    notice.value = (
                        f"OCR tamam · {seller or 'satıcı'}"
                        + (f" · KDV {kdv}" if kdv is not None else "")
                        + " · tutarı doğrula."
                    )
                page.update()
        except Exception as error:
            notice.value = f"Fotoğraf çekilemedi: {str(error)[:100]}"
            page.update()

    async def upload_files():
        try:
            picked = await file_picker.pick_files(
                dialog_title="Fiş / fatura seç",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=ALLOWED_EXTENSIONS,
                allow_multiple=True,
                with_data=True,
            )
            for item in picked:
                data = item.bytes
                extension = Path(item.name).suffix.lower()
                mime = (
                    "application/pdf"
                    if extension == ".pdf"
                    else ("text/plain" if extension in {".txt", ".csv"} else "image/jpeg")
                )
                if not add_attachment(item.name, data, mime):
                    continue
                notice.value = f"{item.name} okunuyor…"
                page.update()
                result = await analyze_attachment(item.name, data, mime)
                apply_parsed(
                    {
                        "type": result.get("type", "expense"),
                        "amount": result.get("amount"),
                        "title": result.get("title"),
                        "customer": "",
                        "summary": result.get("title"),
                        "confidence": 0.8 if result.get("amount") else 0.4,
                    }
                )
                notice.value = result.get("error") or "Öneri dolduruldu. Kaydetmeden önce doğrula."
            refresh_evidence_label()
            page.update()
        except Exception as error:
            notice.value = f"Dosya seçilemedi: {str(error)[:100]}"
            page.update()

    def clear_attachments():
        attachments.clear()
        refresh_evidence_label()
        notice.value = "Ekler temizlendi."
        page.update()

    async def focus_dictation():
        await voice_text.focus()
        notice.value = "Klavye mikrofonuna basıp konuş: “Ahmet'e 450 TL veresiye yaz”."
        page.update()

    async def save_entry():
        values = {
            "type": selected_type["value"],
            "amount": amount.value or "",
            "title": title.value or "",
            "customer": customer.value or "",
            "due_date": due_date.value or "",
            "attachments": list(attachments),
        }
        if await submit("intake", values, None):
            page.pop_dialog()

    async def cleanup():
        if camera_ready["value"]:
            try:
                await camera.pause_preview()
            except Exception:
                pass
            camera_ready["value"] = False

    capture_button = ft.Button(
        content="Fotoğrafı oku",
        on_click=capture_photo,
        bgcolor=TEAL,
        color="white",
        disabled=True,
    )

    quick_row = ft.Row(
        spacing=10,
        controls=[
            big_choice("Aldım", "Kasaya para girdi", lambda e: select_type("income"), tone="teal"),
            big_choice("Verdim", "Kasadan para çıktı", lambda e: select_type("expense"), tone="red"),
        ],
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#F4F8F7",
        title=ft.Text("Defter gibi kayıt", color=INK, weight=ft.FontWeight.BOLD, size=22),
        content=ft.Column(
            width=400,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            controls=[
                quick_row,
                ft.Container(
                    padding=12,
                    border_radius=18,
                    bgcolor=WHITE,
                    border=ft.Border.all(1, "#DCE8E4"),
                    content=ft.Column(
                        spacing=8,
                        tight=True,
                        controls=[
                            ft.Text("Tek dokunuş", color=INK, weight=ft.FontWeight.W_700),
                            type_row,
                            ft.TextButton(content="Veresiye yaz", on_click=lambda e: select_type("debt")),
                        ],
                    ),
                ),
                ft.Container(
                    padding=14,
                    border_radius=18,
                    gradient=ft.LinearGradient(colors=["#0B1C2C", "#168F79"]),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Sesle kayıt", color=WHITE, weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(
                                "Dükkandayken yazma. Konuş: “Ahmet Yılmaz'a 450 TL veresiye yaz”",
                                color="#D7F5EE",
                                size=12,
                            ),
                            voice_text,
                            ft.TextButton(
                                content="Mikrofon alanına geç",
                                on_click=focus_dictation,
                                style=ft.ButtonStyle(color=WHITE),
                            ),
                            summary,
                        ],
                    ),
                ),
                ft.Text("Fiş / fatura", color=INK, weight=ft.FontWeight.W_700),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(content="Kamerayla oku", on_click=open_camera, bgcolor="#EAF2FF", color=INK),
                        ft.Button(content="Galeriden / PDF", on_click=upload_files, bgcolor="#F2F5F4", color=INK),
                        ft.TextButton(content="Ekleri temizle", on_click=clear_attachments),
                    ],
                ),
                camera,
                capture_button,
                evidence_label,
                amount,
                title,
                customer,
                due_date,
                notice,
                ft.Text(
                    "Fotoğraf OCR internet gerektirir (ücretsiz kota). Metinli PDF cihazda okunur. Ses, cihaz klavyesinin mikrofonuyla alınır; Nakitçe ses dosyası kaydetmez.",
                    color=MUTED,
                    size=11,
                ),
            ],
        ),
        actions=[
            ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
            ft.Button(content="Kaydı oluştur", on_click=save_entry, bgcolor=TEAL, color="white"),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=cleanup,
    )
    page.show_dialog(dialog)
