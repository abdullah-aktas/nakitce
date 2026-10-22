import asyncio
import base64
import logging
from datetime import date, timedelta
from urllib.parse import quote

import flet as ft

from exports import csv_report, pdf_bytes, quote_lines, report_lines
from billing_bridge import BillingBridge, PRODUCT_MONTHLY
from membership import BASIC_LIMITS, current_plan, membership_summary, premium_access, trial_days_left
from membership_api import MembershipApiError, MembershipClient
from cloud_sync import CloudSync
from storage import load_evidence, load_records, load_workspace, save_evidence, save_records, save_workspace
from views import business, customers, dashboard, intake, inventory, ledger, tools
from views.common import CANVAS, INK, MUTED, TEAL, WHITE
from views.forms import show_form

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")

TABS = [("home", "Özet"), ("ledger", "Hareket"), ("customers", "Veresiye"), ("inventory", "Stok"), ("tools", "Araçlar")]
TAB_ICONS = {
    "home": ft.Icons.HOME,
    "ledger": ft.Icons.RECEIPT_LONG,
    "customers": ft.Icons.GROUPS,
    "inventory": ft.Icons.INVENTORY_2,
    "tools": ft.Icons.SETTINGS,
}
GIB_PORTAL_URL = "https://earsivportal.efatura.gov.tr/intragiris.html"


def _number(value):
    cleaned = str(value).strip().replace("₺", "").replace(" ", "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned)


def _integer(value):
    return int(float(str(value).strip().replace(",", ".")))


async def main(page: ft.Page):
    page.title = "Nakitçe"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = CANVAS
    page.padding = 0
    page.spacing = 0

    preferences = ft.SharedPreferences()
    file_picker = ft.FilePicker()
    url_launcher = ft.UrlLauncher()
    billing = BillingBridge(page)
    records = await load_records(preferences)
    evidence = await load_evidence(preferences)
    workspace = await load_workspace(preferences)
    membership_client = MembershipClient(preferences)
    await membership_client.initialize()
    cloud_sync = CloudSync(preferences, records)
    await cloud_sync.initialize()
    active_tab = "home"

    content = ft.Container(expand=True, padding=18)
    status_text = ft.Text("Çevrimdışı kayıt açık · bu cihazda saklanır", size=11, color=MUTED)
    nav = ft.Container(bgcolor=WHITE, padding=ft.Padding.symmetric(horizontal=8, vertical=8))

    def set_status(message):
        status_text.value = message
        page.update()

    async def persist(message="Kaydedildi · bu cihazda saklanıyor"):
        cloud_sync.mark_local_change()
        await save_records(preferences, records)
        await cloud_sync.save_meta()
        log.debug("Saved local records")
        if cloud_sync.session:
            await cloud_sync.sync_now()
            status_text.value = cloud_sync.state["message"]
        else:
            status_text.value = message
        refresh()

    async def sync_and_refresh():
        await cloud_sync.sync_now()
        set_status(cloud_sync.state["message"])
        refresh()

    async def resolve_and_refresh(choice):
        try:
            await cloud_sync.resolve(choice)
            set_status(cloud_sync.state["message"])
        except Exception as error:
            log.warning("Could not resolve cloud conflict: %s", error)
            cloud_sync.state["message"] = "Eşitleme tamamlanamadı. Bağlantıyı kontrol edip yeniden dene."
            set_status(cloud_sync.state["message"])
        refresh()

    def premium_active():
        # Live server status first; SharedPreferences cache is UI-only fallback.
        live = membership_client.status
        if live and live.get("from_cache") is not True:
            return premium_access(live, allow_cache=False)
        return premium_access(live, allow_cache=True)

    def require_premium(feature):
        if premium_active():
            return True
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Premium özelliği", color=INK, weight=ft.FontWeight.BOLD),
                content=ft.Text(f"{feature} Premium kapsamındadır. Erişim yalnızca sunucuda doğrulanmış üyelikle açılır.", color=MUTED),
                actions=[
                    ft.TextButton(content="Kapat", on_click=lambda e: page.pop_dialog()),
                    ft.Button(content="Üyelik bilgisi", on_click=lambda e: (page.pop_dialog(), open_membership())),
                ],
            )
        )
        return False

    def ensure_basic_capacity(limit_name, current_value):
        if premium_active() or current_value < BASIC_LIMITS[limit_name]:
            return True
        return require_premium("Temel üyelik sınırını aşan kullanım")

    def show(kind, subject=None):
        if kind in {"pos", "quote", "sync"} and not require_premium(kind):
            return
        if kind in {"income", "expense", "debt", "intake"}:
            intake.show(
                page,
                file_picker,
                process_form,
                evidence,
                initial_type=kind if kind in {"income", "expense", "debt"} else "income",
            )
        else:
            show_form(page, kind, process_form, subject)

    async def save_workspace_state(message):
        await save_workspace(preferences, workspace)
        set_status(message)
        refresh()

    async def save_profile(values):
        workspace["profile"] = values
        await save_workspace_state("İşletme profili kaydedildi. Premium denemesi için doğrulanmış Nakitçe hesabı gerekir.")
        return True

    async def save_reminder(values):
        today = date.today()
        active_reminders = sum(
            1 for item in workspace["reminders"]
            if item.get("date", "") >= today.isoformat()
        )
        if not ensure_basic_capacity("reminders", active_reminders):
            return False
        try:
            due_date = date.fromisoformat(values["date"].strip())
        except ValueError:
            set_status("Tarihi YYYY-AA-GG biçiminde gir.")
            return False
        if not values["title"].strip():
            set_status("Hatırlatma başlığını yaz.")
            return False
        reminder_id = max((int(item.get("id", 0)) for item in workspace["reminders"]), default=0) + 1
        workspace["reminders"].append(
            {
                "id": reminder_id,
                "title": values["title"].strip(),
                "date": due_date.isoformat(),
                "note": values.get("note", "").strip(),
                "sector": workspace.get("profile", {}).get("sector", ""),
            }
        )
        await save_workspace_state("Hatırlatma kaydedildi; ana ekranda tarihine göre görünür.")
        return True

    def open_profile():
        business.show_profile(page, workspace.get("profile", {}), save_profile)

    def open_membership():
        view_state = dict(workspace)
        view_state["premium_access"] = premium_active()
        view_state["server_status"] = membership_client.status
        view_state["trial_days_left"] = trial_days_left(membership_client.status)
        view_state["plan"] = current_plan(membership_client.status)
        view_state["membership_label"] = membership_summary(membership_client.status)
        view_state["signed_in"] = membership_client.signed_in
        view_state["configured"] = membership_client.configured
        view_state["email"] = (
            membership_client.session.get("user", {}).get("email")
            or workspace.get("profile", {}).get("email", "")
        )
        view_state["message"] = membership_client.message
        business.show_membership(
            page,
            view_state,
            change_mode,
            membership_action,
            refresh_membership_status,
            on_purchase=lambda: asyncio.create_task(purchase_premium()),
        )

    async def membership_action(action, email, password):
        try:
            if action == "sign_up":
                result = await membership_client.sign_up(email, password)
            elif action == "sign_in":
                result = await membership_client.sign_in(email, password)
            elif action == "sign_out":
                await membership_client.sign_out()
                result = "Oturum kapatıldı."
            else:
                return
            set_status(result)
            refresh()
        except MembershipApiError as error:
            set_status(str(error))

    async def refresh_membership_status():
        try:
            await membership_client.refresh_status()
            set_status("Üyelik durumu sunucudan doğrulandı.")
        except MembershipApiError as error:
            membership_client.status = None
            set_status(str(error))
        refresh()

    def open_reminder():
        sector = workspace.get("profile", {}).get("sector", "")
        business.show_reminder(page, save_reminder, sector)

    def change_mode(mode):
        if mode == "advanced" and not premium_active():
            open_membership()
            return
        page.pop_dialog()
        workspace["mode"] = mode
        asyncio.create_task(save_workspace_state("Ekran modu güncellendi."))

    def tab_label(key):
        sector = workspace.get("profile", {}).get("sector", "")
        if key == "inventory":
            if sector in {"Berber / kuaför", "Serbest meslek"}:
                return "Hizmetler"
            if sector in {"Marangoz / mobilya", "Tesisat / teknik servis"}:
                return "Malzeme"
            return "Stok"
        if key == "customers":
            return "Müşteriler" if sector in {"Berber / kuaför", "Serbest meslek", "Tesisat / teknik servis"} else "Veresiye"
        return dict(TABS).get(key, key)

    def render_nav():
        nav.content = ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=5,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                    border_radius=14,
                    bgcolor=TEAL if key == active_tab else WHITE,
                    on_click=lambda e, selected=key: select_tab(selected),
                    tooltip=label,
                    content=ft.Row(
                        tight=True,
                        spacing=7,
                        controls=[
                            ft.Icon(TAB_ICONS[key], size=17, color=WHITE if key == active_tab else MUTED),
                            ft.Text(label, color=WHITE if key == active_tab else MUTED, weight=ft.FontWeight.W_600, size=13),
                        ],
                    ),
                )
                for key, label in [(item[0], tab_label(item[0])) for item in TABS]
            ],
        )

    def select_tab(selected):
        nonlocal active_tab
        active_tab = selected
        refresh()

    async def process_form(kind, values, subject):
        try:
            if kind in {"sync", "pos", "quote"} and not premium_active():
                require_premium(kind)
                return False
            if kind in {"intake", "income", "expense", "debt", "collect", "sale"}:
                month_key = date.today().strftime("%Y-%m")
                month_count = sum(1 for item in records["transactions"] if item.get("date", "").startswith(month_key))
                if not ensure_basic_capacity("monthly_transactions", month_count):
                    return False
            if kind == "customer" and len(records["customers"]) >= BASIC_LIMITS["customers"] and not premium_active():
                require_premium("Daha fazla müşteri kaydı")
                return False
            if kind == "product" and len(records["products"]) >= BASIC_LIMITS["products"] and not premium_active():
                require_premium("Daha fazla ürün kaydı")
                return False

            if kind == "sync":
                await cloud_sync.connect(values)
                status_text.value = cloud_sync.state["message"]
                refresh()
                return True

            if kind == "intake":
                if values.get("attachments") and not premium_active():
                    require_premium("Fotoğraf ve belgeyi kayıtla saklama")
                    return False
                amount = _number(values["amount"])
                if amount <= 0:
                    raise ValueError("Tutar sıfırdan büyük olmalı.")
                entry_type = values["type"]
                if entry_type not in {"income", "expense", "debt"}:
                    raise ValueError("Kayıt türünü seç.")
                title = values["title"].strip() or ("Gelen para" if entry_type == "income" else "Giden para")
                transaction_id = max((int(t.get("id", 0)) for t in records["transactions"]), default=0) + 1
                transaction = {
                    "id": transaction_id,
                    "type": entry_type,
                    "title": title,
                    "amount": amount,
                    "date": date.today().isoformat(),
                }
                if entry_type == "debt":
                    customer_name = values["customer"].strip()
                    if not customer_name:
                        raise ValueError("Veresiye kaydı için müşteri adını yaz.")
                    customer_record = next(
                        (c for c in records["customers"] if c["name"].casefold() == customer_name.casefold()),
                        None,
                    )
                    if customer_record is None:
                        if len(records["customers"]) >= BASIC_LIMITS["customers"] and not premium_active():
                            require_premium("Daha fazla müşteri kaydı")
                            return False
                        customer_id = max((int(c.get("id", 0)) for c in records["customers"]), default=0) + 1
                        customer_record = {"id": customer_id, "name": customer_name, "phone": "", "balance": 0.0}
                        records["customers"].append(customer_record)
                    customer_record["balance"] += amount
                    transaction["title"] = f"Veresiye · {customer_record['name']} · {title}"
                else:
                    records["cash_balance"] += amount if entry_type == "income" else -amount
                records["transactions"].append(transaction)
                attached = values.get("attachments", [])
                if attached:
                    evidence[str(transaction_id)] = [
                        {
                            "name": item["name"],
                            "mime": item["mime"],
                            "data": base64.b64encode(item["bytes"]).decode("ascii"),
                        }
                        for item in attached
                    ]
                    await save_evidence(preferences, evidence)

            elif kind in {"income", "expense"}:
                amount = _number(values["amount"])
                if amount <= 0:
                    raise ValueError("Tutar sıfırdan büyük olmalı.")
                entry_type = "income" if kind == "income" else "expense"
                title = values["title"].strip() or ("Gelen para" if entry_type == "income" else "Giden para")
                records["transactions"].append({"id": int(date.today().strftime("%Y%m%d")) + len(records["transactions"]), "type": entry_type, "title": title, "amount": amount, "date": date.today().isoformat()})
                records["cash_balance"] += amount if entry_type == "income" else -amount

            elif kind == "debt":
                amount = _number(values["amount"])
                name = values["name"].strip()
                if amount <= 0 or not name:
                    raise ValueError("Müşteri adı ve sıfırdan büyük tutar gerekli.")
                customer = next((c for c in records["customers"] if c["name"].casefold() == name.casefold()), None)
                if customer is None:
                    if len(records["customers"]) >= BASIC_LIMITS["customers"] and not premium_active():
                        require_premium("Daha fazla müşteri kaydı")
                        return False
                    customer = {"id": len(records["customers"]) + 1, "name": name, "phone": "", "balance": 0.0}
                    records["customers"].append(customer)
                customer["balance"] += amount
                records["transactions"].append({"id": len(records["transactions"]) + 1, "type": "debt", "title": f"Veresiye · {customer['name']}", "amount": amount, "date": date.today().isoformat()})

            elif kind == "collect":
                amount = _number(values["amount"])
                if amount <= 0:
                    raise ValueError("Tahsilat tutarı sıfırdan büyük olmalı.")
                customer = next(c for c in records["customers"] if c["id"] == subject["id"])
                if amount > customer["balance"]:
                    raise ValueError("Tahsilat, müşterinin açık bakiyesinden fazla olamaz.")
                customer["balance"] -= amount
                records["cash_balance"] += amount
                records["transactions"].append({"id": len(records["transactions"]) + 1, "type": "income", "title": f"Tahsilat · {customer['name']}", "amount": amount, "date": date.today().isoformat()})

            elif kind == "customer":
                name = values["name"].strip()
                if not name:
                    raise ValueError("Müşteri adını yaz.")
                if any(c["name"].casefold() == name.casefold() for c in records["customers"]):
                    raise ValueError("Bu müşteri zaten kayıtlı.")
                records["customers"].append({"id": len(records["customers"]) + 1, "name": name, "phone": values["phone"].strip(), "balance": 0.0})

            elif kind == "product":
                name = values["name"].strip()
                if not name:
                    raise ValueError("Ürün veya hizmet adını yaz.")
                qty = _integer(values["qty"] or "0")
                min_qty = _integer(values["min_qty"] or "0")
                price = _number(values["price"] or "0")
                if qty < 0 or min_qty < 0 or price < 0:
                    raise ValueError("Stok, uyarı seviyesi ve fiyat negatif olamaz.")
                records["products"].append({"id": len(records["products"]) + 1, "name": name, "barcode": values["barcode"].strip(), "qty": qty, "min_qty": min_qty, "price": price})

            elif kind == "sale":
                product = next(p for p in records["products"] if p["id"] == subject["id"])
                qty = _integer(values["qty"])
                if qty <= 0:
                    raise ValueError("Satış adedi sıfırdan büyük olmalı.")
                if product["min_qty"] > 0 and qty > product["qty"]:
                    raise ValueError("Stokta bu kadar ürün yok.")
                amount = round(product["price"] * qty, 2)
                if product["min_qty"] > 0:
                    product["qty"] -= qty
                records["cash_balance"] += amount
                records["transactions"].append({"id": len(records["transactions"]) + 1, "type": "income", "title": f"Satış · {product['name']} × {qty}", "amount": amount, "date": date.today().isoformat()})

            elif kind == "lookup":
                barcode = values["barcode"].strip()
                product = next((p for p in records["products"] if p.get("barcode") == barcode and barcode), None)
                if product is None:
                    set_status("Bu barkodla eşleşen ürün bulunamadı.")
                else:
                    set_status(f"Bulundu: {product['name']} · stok {product['qty']} · {product['price']:.2f} TL. Satış için Stok sekmesine geç.")
                return True

            elif kind == "pos":
                gross = _number(values["gross"])
                rate = _number(values["rate"])
                days = _integer(values["days"])
                if gross <= 0 or rate < 0 or rate > 100 or days < 0:
                    raise ValueError("Tutar pozitif olmalı; kesinti %0–100, gün sayısı sıfır veya daha büyük olmalı.")
                net = round(gross * (1 - rate / 100), 2)
                pos_id = len(records["pos"]) + 1
                records["pos"].append({"id": pos_id, "bank": values["bank"].strip() or "POS", "gross": gross, "rate": rate, "days": days, "date": (date.today() + timedelta(days=days)).isoformat(), "net": net, "paid": False})

            elif kind == "quote":
                customer = values["customer"].strip()
                title = values["title"].strip()
                if not customer or not title:
                    raise ValueError("Müşteri ve yapılacak iş alanlarını doldur.")
                materials = _number(values["materials"] or "0")
                labor = _number(values["labor"] or "0")
                if materials < 0 or labor < 0:
                    raise ValueError("Malzeme ve işçilik tutarı negatif olamaz.")
                records["quotes"].append({"id": len(records["quotes"]) + 1, "customer": customer, "title": title, "materials": materials, "labor": labor, "date": date.today().isoformat()})

            await persist()
            return True
        except (ValueError, StopIteration, KeyError) as error:
            set_status(str(error) or "Bilgileri kontrol edip tekrar dene.")
            return False

    async def mark_pos(item):
        if not require_premium("POS takibi"):
            return
        pos = next((p for p in records["pos"] if p["id"] == item["id"]), None)
        if pos is None:
            return
        pos["paid"] = not pos["paid"]
        if pos["paid"]:
            records["cash_balance"] += pos["net"]
            records["transactions"].append({"id": len(records["transactions"]) + 1, "type": "income", "title": f"POS'tan geldi · {pos['bank']}", "amount": pos["net"], "date": date.today().isoformat(), "pos_id": pos["id"]})
        else:
            records["cash_balance"] -= pos["net"]
            records["transactions"] = [t for t in records["transactions"] if t.get("pos_id") != pos["id"]]
        await persist("POS durumu güncellendi · cihazda saklanıyor")

    async def open_gib(e):
        try:
            await url_launcher.launch_url(GIB_PORTAL_URL)
            set_status("GİB e-Arşiv portalı açıldı. Giriş ve SMS onayını resmi portalda tamamla.")
        except Exception as error:
            log.warning("GİB portal could not be opened: %s", error)
            set_status("GİB portalı açılamadı. İnternet bağlantısını kontrol et veya bağlantıyı tarayıcıda aç.")

    async def send_reminder(customer):
        phone = "".join(char for char in customer.get("phone", "") if char.isdigit())
        amount_text = f"{customer['balance']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        message = f"Merhaba {customer['name']}, {amount_text} TL tutarındaki veresiye bakiyenizi hatırlatmak isteriz. Teşekkür ederiz."
        try:
            await url_launcher.launch_url(f"https://wa.me/{phone}?text={quote(message)}")
            set_status("WhatsApp'ta hatırlatma taslağı açıldı; göndermeden önce kontrol et.")
        except Exception as error:
            log.warning("WhatsApp could not be opened: %s", error)
            set_status("WhatsApp açılamadı. Telefon numarasını ve cihaz bağlantısını kontrol et.")

    async def save_file(name, content):
        try:
            result = await file_picker.save_file(file_name=name, src_bytes=content)
            set_status("Dosya hazırlandı." if result is not None else "Dosya kaydetme penceresi kapatıldı.")
        except Exception as error:
            log.exception("Export failed")
            set_status(f"Dosya oluşturulamadı: {error}")

    async def export_evidence(item):
        try:
            await file_picker.save_file(
                file_name=item["name"],
                src_bytes=base64.b64decode(item["data"]),
            )
            set_status("Belge bu cihaza aktarıldı.")
        except Exception as error:
            log.warning("Could not export attachment: %s", error)
            set_status("Belge dışa aktarılamadı.")

    def show_evidence(transaction_id):
        attachments = evidence.get(str(transaction_id), [])
        if not attachments:
            set_status("Bu kayda bağlı belge bulunamadı.")
            return
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Kayda eklenen belgeler", color=INK, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.TextButton(
                        content=f"{item['name']} · indir",
                        on_click=lambda e, selected=item: asyncio.create_task(export_evidence(selected)),
                    )
                    for item in attachments
                ],
            ),
            actions=[ft.TextButton(content="Kapat", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(dialog)

    async def export_quote(quote_record):
        if not require_premium("Teklif PDF'i"):
            return
        await save_file("teklif.pdf", pdf_bytes(quote_lines(quote_record)))

    async def export_pdf():
        period = date.today().strftime("%Y_%m")
        await save_file(f"nakitce_{period}_isletme_raporu.pdf", pdf_bytes(report_lines(records, workspace.get("profile", {}))))

    async def export_csv():
        period = date.today().strftime("%Y_%m")
        await save_file(f"nakitce_{period}_isletme_raporu.csv", csv_report(records, workspace.get("profile", {})))

    async def purchase_premium():
        if not membership_client.signed_in:
            set_status("Önce Nakitçe hesabına giriş yap.")
            open_membership()
            return
        token = await billing.launch_purchase(PRODUCT_MONTHLY)
        if not token:
            set_status("Google Play Billing köprüsü henüz bağlı değil; satın alma sunucuya gönderilemedi.")
            return
        try:
            await membership_client.verify_play_purchase(token, PRODUCT_MONTHLY)
            set_status("Satın alma sunucuda doğrulandı.")
        except MembershipApiError as error:
            set_status(str(error))
        refresh()

    def start_pos_toggle(item):
        if require_premium("POS takibi"):
            asyncio.create_task(mark_pos(item))

    def start_reminder(customer):
        asyncio.create_task(send_reminder(customer))

    def start_quote_pdf(item):
        asyncio.create_task(export_quote(item))

    def start_csv():
        asyncio.create_task(export_csv())

    def start_pdf():
        asyncio.create_task(export_pdf())

    actions = {
        "income": lambda e: show("income"),
        "expense": lambda e: show("expense"),
        "debt": lambda e: show("debt"),
        "sale": lambda e: select_tab("inventory"),
        "add": lambda e: show("customer"),
        "collect": lambda customer: show("collect", customer),
        "remind": start_reminder,
        "product_add": lambda e: show("product"),
        "sell": lambda product: show("sale", product),
        "lookup": lambda e: show("lookup"),
        "add_pos": lambda e: show("pos"),
        "toggle_pos": start_pos_toggle,
        "add_quote": lambda e: show("quote"),
        "quote_pdf": start_quote_pdf,
        "export_csv": lambda e: start_csv(),
        "export_pdf": lambda e: start_pdf(),
        "open_gib": open_gib,
        "evidence": show_evidence,
        "sync_setup": lambda e: show("sync", cloud_sync.config),
        "sync_now": lambda e: asyncio.create_task(sync_and_refresh()) if require_premium("Bulut eşitleme") else None,
        "sync_upload": lambda e: asyncio.create_task(resolve_and_refresh("upload")) if require_premium("Bulut eşitleme") else None,
        "sync_download": lambda e: asyncio.create_task(resolve_and_refresh("download")) if require_premium("Bulut eşitleme") else None,
        "edit_profile": lambda e: open_profile(),
        "membership": lambda e: open_membership(),
        "add_reminder": lambda e: open_reminder(),
    }

    def refresh():
        if not premium_active() and workspace.get("mode") == "advanced":
            workspace["mode"] = "simple"
            asyncio.create_task(save_workspace(preferences, workspace))
        view_workspace = dict(workspace)
        view_workspace["_server_membership_status"] = membership_client.status
        builders = {
            "home": lambda: dashboard.build(records, actions, view_workspace),
            "ledger": lambda: ledger.build(records, actions, evidence),
            "customers": lambda: customers.build(records, actions),
            "inventory": lambda: inventory.build(records, actions),
            "tools": lambda: tools.build(records, actions, cloud_sync.state, view_workspace),
        }
        content.content = builders[active_tab]()
        render_nav()
        page.update()

    header = ft.Container(
        padding=ft.Padding.only(left=18, right=18, top=18, bottom=10),
        content=ft.Row(
            controls=[
                ft.Image(src="logo.svg", width=176, height=46, fit=ft.BoxFit.CONTAIN, semantics_label="Nakitçe · Esnafın cep defteri"),
                ft.Container(expand=True),
                ft.Text("●", color=TEAL, size=13),
            ]
        ),
    )
    status_bar = ft.Container(padding=ft.Padding.symmetric(horizontal=18, vertical=5), content=status_text)
    root = ft.Column(expand=True, spacing=0, controls=[header, status_bar, content, nav])
    page.add(root)
    refresh()
    if not workspace.get("profile", {}).get("business_name"):
        business.show_profile(page, workspace.get("profile", {}), save_profile)

    asyncio.create_task(cloud_sync.retry_loop())
    log.info("Nakitçe opened with %d customers and %d transactions", len(records["customers"]), len(records["transactions"]))


ft.run(main)
