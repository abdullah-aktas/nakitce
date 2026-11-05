"""Kamera ile barkod tarama + elle giriş."""

from __future__ import annotations

import asyncio

import flet as ft

from barcode_decode import decode_barcode_bytes
from views.common import INK, MUTED, TEAL, WHITE, camera_supported


def show(page, on_code, *, title="Barkod tara"):
    """on_code(barcode: str) async veya sync çağrılır."""
    use_camera = camera_supported(page)
    camera = None
    camera_ready = {"value": False}
    streaming = {"value": False}
    found = {"value": False}
    frame_i = {"n": 0}

    if use_camera:
        from flet_camera import Camera, CameraLensDirection, ImageFormatGroup, ResolutionPreset

        camera = Camera(width=360, height=260, visible=False)

    barcode_field = ft.TextField(
        label="Barkod numarası",
        hint_text="Kamerayla oku veya elle yaz" if use_camera else "Barkod numarasını yaz",
        keyboard_type=ft.KeyboardType.NUMBER,
        filled=True,
        bgcolor=WHITE,
        autofocus=not use_camera,
    )
    notice = ft.Text(
        "Barkodu kadraja al. Otomatik okunmazsa “Fotoğrafla oku”ya bas veya numarayı yaz."
        if use_camera
        else "Bu cihazda kamera yok. Barkod numarasını elle yazıp bul.",
        color=MUTED,
        size=12,
    )

    async def stop_stream():
        if camera is None or not streaming["value"]:
            return
        try:
            await camera.stop_image_stream()
        except Exception:
            pass
        streaming["value"] = False

    async def cleanup():
        await stop_stream()
        if camera is not None and camera_ready["value"]:
            try:
                await camera.pause_preview()
            except Exception:
                pass
            camera_ready["value"] = False

    async def finish(code: str):
        code = (code or "").strip()
        if not code or found["value"]:
            return
        found["value"] = True
        barcode_field.value = code
        notice.value = f"Okundu: {code}"
        page.update()
        await stop_stream()
        try:
            result = on_code(code)
            if asyncio.iscoroutine(result):
                await result
        finally:
            page.pop_dialog()

    async def on_stream_image(e):
        if found["value"] or not streaming["value"]:
            return
        frame_i["n"] += 1
        if frame_i["n"] % 6 != 0:
            return
        data = getattr(e, "bytes", None) or b""
        code = decode_barcode_bytes(data)
        if code:
            await finish(code)

    if camera is not None:
        camera.on_stream_image = on_stream_image

    async def open_camera():
        if not use_camera or camera is None:
            notice.value = "Bu cihazda kamera desteklenmiyor. Numarayı elle yaz."
            page.update()
            return
        camera.visible = True
        notice.value = "Kamera açılıyor…"
        page.update()
        try:
            cameras = await camera.get_available_cameras()
            if not cameras:
                raise RuntimeError("Kullanılabilir kamera yok.")
            description = next(
                (item for item in cameras if item.lens_direction == CameraLensDirection.BACK),
                cameras[0],
            )
            await camera.initialize(
                description=description,
                resolution_preset=ResolutionPreset.MEDIUM,
                enable_audio=False,
                image_format_group=ImageFormatGroup.JPEG,
            )
            camera_ready["value"] = True
            capture_btn.disabled = False
            notice.value = "Barkodu çerçeveye getir — otomatik tarama açık."
            page.update()
            can_stream = False
            try:
                can_stream = await camera.supports_image_streaming()
            except Exception:
                can_stream = False
            if can_stream:
                await camera.start_image_stream()
                streaming["value"] = True
                notice.value = "Canlı tarama açık. Barkodu tut, okuyunca satışa geçilir."
            else:
                notice.value = "Canlı akış yok. “Fotoğrafla oku” ile çek."
        except Exception as error:
            camera.visible = False
            notice.value = (
                f"Kamera açılamadı ({str(error)[:90]}). "
                "Numarayı elle yazabilirsin."
            )
        page.update()

    async def capture_and_decode():
        if found["value"] or camera is None:
            return
        if not camera_ready["value"]:
            await open_camera()
            if not camera_ready["value"]:
                return
        notice.value = "Fotoğraf çekiliyor…"
        page.update()
        try:
            data = await camera.take_picture()
            code = decode_barcode_bytes(data)
            if code:
                await finish(code)
            else:
                notice.value = "Barkod okunamadı. Daha net çek veya numarayı elle gir."
                page.update()
        except Exception as error:
            notice.value = f"Çekim başarısız: {str(error)[:100]}"
            page.update()

    async def submit_manual(e=None):
        code = (barcode_field.value or "").strip()
        if not code:
            notice.value = "Barkod numarası yaz" + (" veya kamerayla oku." if use_camera else ".")
            page.update()
            return
        await finish(code)

    async def on_dismiss(e=None):
        await cleanup()

    capture_btn = ft.Button(
        content="Fotoğrafla oku",
        on_click=capture_and_decode,
        bgcolor=TEAL,
        color="white",
        disabled=True,
        visible=use_camera,
    )

    row_controls = []
    if use_camera:
        row_controls.extend(
            [
                ft.Button(content="Kamerayı aç", on_click=open_camera, bgcolor="#EAF2FF", color=INK),
                capture_btn,
            ]
        )

    content_controls = [
        ft.Text(
            "Ürün barkodunu kameraya göster (EAN-13, Code128, QR…)."
            if use_camera
            else "Barkod numarasını yazıp stokta ara.",
            color=MUTED,
            size=12,
        ),
    ]
    if row_controls:
        content_controls.append(ft.Row(wrap=True, spacing=8, controls=row_controls))
    if camera is not None:
        content_controls.append(camera)
    content_controls.extend([barcode_field, notice])

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#F4F8F7",
        title=ft.Text(title, color=INK, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            width=380,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=content_controls,
        ),
        actions=[
            ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
            ft.Button(content="Numarayla bul", on_click=submit_manual, bgcolor=TEAL, color="white"),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=on_dismiss,
    )
    page.show_dialog(dialog)
    if use_camera:
        asyncio.create_task(open_camera())
