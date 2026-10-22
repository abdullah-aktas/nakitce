import base64
from datetime import datetime
from pathlib import Path

import flet as ft
from flet_camera import Camera, CameraLensDirection, ResolutionPreset

from intake_text import extract_pdf_text, parse_intake_text
from views.common import INK, MUTED, TEAL

MAX_FILE_BYTES = 1_000_000
MAX_EVIDENCE_BYTES = 2_000_000
ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp", "txt", "csv"]


def show(page, file_picker, submit, saved_evidence, initial_type="income"):
    selected_type = {"value": initial_type if initial_type in {"income", "expense", "debt"} else "income"}
    attachments = []
    camera = Camera(width=340, height=230, visible=False)
    camera_ready = {"value": False}
    existing_size = sum(
        len(base64.b64decode(item.get("data", "")))
        for items in saved_evidence.values()
        for item in items
    )

    voice_text = ft.TextField(
        label="Konuşarak anlat veya not yaz",
        hint_text="Örn. Gelen para 1250 günlük satış",
        multiline=True,
        min_lines=2,
        max_lines=4,
        on_change=None,
    )
    amount = ft.TextField(label="Tutar (TL)", keyboard_type=ft.KeyboardType.NUMBER)
    title = ft.TextField(label="Açıklama")
    customer = ft.TextField(label="Müşteri adı · veresiye için", visible=False)
    notice = ft.Text("", color=MUTED, size=12)
    evidence_label = ft.Text("Henüz fotoğraf veya belge eklenmedi.", color=MUTED, size=12)
    type_buttons = {}

    def refresh_type_buttons():
        for kind, button in type_buttons.items():
            button.bgcolor = TEAL if selected_type["value"] == kind else "#F2F5F4"
            button.color = "white" if selected_type["value"] == kind else INK
        customer.visible = selected_type["value"] == "debt"
        page.update()

    def select_type(kind):
        selected_type["value"] = kind
        refresh_type_buttons()

    type_row = ft.Row(wrap=True, spacing=8)
    for kind, label in (("income", "Gelen para"), ("expense", "Giden para"), ("debt", "Veresiye")):
        button = ft.Button(
            content=label,
            on_click=lambda e, k=kind: select_type(k),
            bgcolor=TEAL if kind == selected_type["value"] else "#F2F5F4",
            color="white" if kind == selected_type["value"] else INK,
        )
        type_buttons[kind] = button
        type_row.controls.append(button)

    def refresh_evidence_label():
        if attachments:
            names = " · ".join(item["name"] for item in attachments)
            evidence_label.value = f"Eklenenler ({len(attachments)}): {names}"
        else:
            evidence_label.value = "Henüz fotoğraf veya belge eklenmedi."
        page.update()

    def current_attachment_bytes():
        return sum(len(item["bytes"]) for item in attachments)

    def add_attachment(name, data, mime):
        size = len(data or b"")
        if not size:
            notice.value = "Dosya içeriği okunamadı. Tekrar seçip dene."
            page.update()
            return False
        if size > MAX_FILE_BYTES:
            notice.value = "Her dosya en fazla 1 MB olabilir. Daha küçük bir dosya seç."
            page.update()
            return False
        if existing_size + current_attachment_bytes() + size > MAX_EVIDENCE_BYTES:
            notice.value = "Bu cihazdaki belge alanı doldu (toplam 2 MB). Eski ekleri indirip cihazdan temizlemeden yenisi eklenemez."
            page.update()
            return False
        attachments.append({"name": name, "mime": mime, "bytes": data})
        notice.value = "Eklendi. Kaydetmeden önce tutar ve açıklamayı kontrol et."
        refresh_evidence_label()
        return True

    def apply_suggestion(text, filename=""):
        suggestion = parse_intake_text(text, filename)
        selected_type["value"] = suggestion["type"]
        if suggestion["amount"] is not None:
            amount.value = str(suggestion["amount"])
        if suggestion["title"]:
            title.value = suggestion["title"][:120]
        customer.visible = selected_type["value"] == "debt"
        refresh_type_buttons()

    def on_voice_text_change(e):
        apply_suggestion(e.control.value)
        notice.value = "Önerilen tür ve tutar dolduruldu. Kaydetmeden önce doğrula; miktar kelimeyle söylendiyse tutarı elle gir."
        page.update()

    voice_text.on_change = on_voice_text_change

    async def open_camera():
        camera.visible = True
        notice.value = "Kamera açılıyor…"
        page.update()
        try:
            cameras = await camera.get_available_cameras()
            if not cameras:
                raise RuntimeError("Kullanılabilir kamera bulunamadı.")
            description = next(
                (item for item in cameras if item.lens_direction == CameraLensDirection.BACK),
                cameras[0],
            )
            await camera.initialize(
                description=description,
                resolution_preset=ResolutionPreset.LOW,
                enable_audio=False,
            )
            camera_ready["value"] = True
            capture_button.disabled = False
            notice.value = "Belgeyi kadraja al ve fotoğraf çek."
        except Exception as error:
            log_message = str(error)
            camera.visible = False
            notice.value = f"Kamera açılamadı. İzinleri kontrol et veya belge yükle. ({log_message[:100]})"
        page.update()

    async def capture_photo():
        if not camera_ready["value"]:
            return
        try:
            data = await camera.take_picture()
            if add_attachment(f"makbuz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg", data, "image/jpeg"):
                camera.visible = False
                await camera.pause_preview()
                camera_ready["value"] = False
                capture_button.disabled = True
                notice.value = "Fotoğraf eklendi. Görselden otomatik OCR yapılmıyor; alanları kendin kontrol edip tamamla."
                page.update()
        except Exception as error:
            notice.value = f"Fotoğraf çekilemedi: {str(error)[:100]}"
            page.update()

    async def upload_files():
        try:
            picked = await file_picker.pick_files(
                dialog_title="Makbuz veya belge seç",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=ALLOWED_EXTENSIONS,
                allow_multiple=True,
                with_data=True,
            )
            for item in picked:
                data = item.bytes
                extension = Path(item.name).suffix.lower()
                mime = "application/pdf" if extension == ".pdf" else (
                    "text/plain" if extension in {".txt", ".csv"} else "image/*"
                )
                if add_attachment(item.name, data, mime) and extension == ".pdf":
                    try:
                        extracted = extract_pdf_text(data)
                        if extracted:
                            voice_text.value = extracted[:3000]
                            apply_suggestion(extracted, item.name)
                            notice.value = "PDF metni okundu; tutar ve tür için öneri dolduruldu. Bilgileri mutlaka doğrula."
                        else:
                            notice.value = "PDF eklendi; içinde seçilebilir metin bulunamadı. Tutarı elle gir."
                    except Exception:
                        notice.value = "PDF eklendi ancak metni okunamadı. Tutarı elle gir."
            refresh_evidence_label()
            page.update()
        except Exception as error:
            notice.value = f"Dosya seçilemedi: {str(error)[:100]}"
            page.update()

    def clear_attachments():
        attachments.clear()
        refresh_evidence_label()
        notice.value = "Taslak ekleri kaldırıldı."
        page.update()

    async def focus_dictation():
        await voice_text.focus()

    async def save_entry():
        values = {
            "type": selected_type["value"],
            "amount": amount.value or "",
            "title": title.value or "",
            "customer": customer.value or "",
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
        content="Fotoğrafı kullan",
        on_click=capture_photo,
        bgcolor=TEAL,
        color="white",
        disabled=True,
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Hareket kaydı", color=INK, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            width=380,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                type_row,
                ft.Text("Giriş seçenekleri", color=INK, weight=ft.FontWeight.W_600),
                ft.Text("Yazarak veya klavye mikrofonuyla dikte ederek anlat. Fotoğraf çek ya da cihazından belge seç; önerilen bilgileri kaydetmeden önce kontrol et.", color=MUTED, size=12),
                voice_text,
                ft.TextButton(content="Yazı alanına geç · klavye mikrofonunu kullan", on_click=focus_dictation),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.Button(content="Fotoğraf çek", on_click=open_camera, bgcolor="#EAF2FF", color=INK),
                        ft.Button(content="Fotoğraf / belge ekle", on_click=upload_files, bgcolor="#F2F5F4", color=INK),
                        ft.TextButton(content="Ekleri temizle", on_click=clear_attachments),
                    ],
                ),
                camera,
                capture_button,
                evidence_label,
                amount,
                title,
                customer,
                notice,
                ft.Text("Metinli PDF'lerde tutar için öneri oluşturulur. Fotoğraflar bu sürümde otomatik okunmaz; ekler cihazda saklanır ve Supabase'e yüklenmez.", color=MUTED, size=11),
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
