import asyncio
import base64
import logging
from datetime import date, timedelta
from urllib.parse import quote

import flet as ft

from bank_import import parse_bank_csv
from exports import csv_report
from pdf_docs import business_report_pdf, customer_statement_pdf, quote_pdf
from billing_bridge import BillingBridge, PRODUCT_MONTHLY
from membership import BASIC_LIMITS, current_plan, membership_summary, premium_access, trial_days_left
from membership_api import MembershipApiError, MembershipClient
from membership_config import PAYMENT_URL, PRICE_TEXT, PRIVACY_URL
from cloud_sync import CloudSync
from reminders_engine import critical_alerts, default_due_date, seed_tax_reminders, whatsapp_reminder_message
from storage import load_evidence, load_records, load_workspace, save_evidence, save_records, save_workspace
from views import barcode_lookup, business, customers, dashboard, intake, inventory, ledger, tools
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
    cleaned = str(value).strip().replace("₺", "").replace("TL", "").replace("tl", "").replace(" ", "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif cleaned.count(".") > 1 or (cleaned.count(".") == 1 and len(cleaned.rsplit(".", 1)[1]) == 3):
        cleaned = cleaned.replace(".", "")  # 1.250 / 1.250.000 → binlik ayracı
    result = float(cleaned)
    if result != result or result in (float("inf"), float("-inf")):
        raise ValueError("Geçerli bir sayı yaz.")
    return result


def _next_id(items):
    return max((int(item.get("id", 0)) for item in items), default=0) + 1


def _normalize_phone(value):
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = "9" + digits
    elif len(digits) == 10 and digits.startswith("5"):
        digits = "90" + digits
    return digits


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
    share = ft.Share()
    clipboard = ft.Clipboard()
    billing = BillingBridge(page)
    records = await load_records(preferences)
    evidence = await load_evidence(preferences)
    workspace = await load_workspace(preferences)
    membership_client = MembershipClient(preferences)
    await membership_client.initialize()
    cloud_sync = CloudSync(preferences, records, workspace)
    await cloud_sync.initialize()
    if membership_client.signed_in:
        cloud_sync.attach_membership(membership_client)
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
        if kind in {"pos", "quote"} and not require_premium(kind):
            return
        if kind == "lookup":
            open_barcode_lookup()
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

    def open_barcode_lookup():
        async def on_code(code):
            code = (code or "").strip()
            product = next(
                (p for p in records["products"] if p.get("barcode") == code and code),
                None,
            )
            if product is None:
                try:
                    await clipboard.set(code)
                except Exception:
                    pass
                set_status(
                    f"Barkod {code} stokta yok. Numara panoya kopyalandı — “+ Ürün” ile ekleyebilirsin."
                )
                show_snack(f"Bulunamadı: {code}", color="#FFF1D8")
                return
            set_status(
                f"Barkod okundu: {product['name']} · stok {product['qty']} · {product['price']:.2f} TL"
            )
            show_snack(f"Okundu: {product['name']}")
            show("sale", product)

        barcode_lookup.show(page, on_code, title="Barkod tara")

    def show_snack(message, *, color=TEAL, text_color=None):
        # Sarı / amber zeminlerde siyah; diğerlerinde beyaz.
        amber_like = {"#FFF1D8", "#FFF6E0", "#FFF9ED", "#FFF5E2", "#E8A317", "#C7922A", "#F6B94A"}
        fg = text_color or (INK if color in amber_like else WHITE)
        try:
            page.show_dialog(ft.SnackBar(content=ft.Text(message, color=fg), bgcolor=color, duration=4500))
        except Exception:
            set_status(message)

    async def save_workspace_state(message):
        cloud_sync.mark_local_change()
        await save_workspace(preferences, workspace)
        await cloud_sync.save_meta()
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
            billing_available=billing.available,
            on_redeem=redeem_code,
            on_delete_account=delete_account,
            on_legal=open_legal,
            on_web_pay=(lambda: asyncio.create_task(url_launcher.launch_url(PAYMENT_URL))) if PAYMENT_URL.startswith("https://") else None,
            price_text=PRICE_TEXT,
        )

    def open_legal():
        business.show_legal(page, PRIVACY_URL, lambda url: asyncio.create_task(url_launcher.launch_url(url)))

    async def redeem_code(code):
        try:
            set_status(await membership_client.redeem_code(code))
            show_snack("Premium süren güncellendi")
        except MembershipApiError as error:
            set_status(str(error))
        refresh()

    def delete_account():
        async def do():
            try:
                await membership_client.delete_account()
                cloud_sync.detach()
                set_status("Hesap ve bulut verileri silindi. Cihazdaki kayıtların duruyor.")
            except MembershipApiError as error:
                set_status(str(error))
            refresh()

        page.pop_dialog()
        confirm("Hesap silinsin mi?", "Hesabın, üyeliğin ve buluttaki verilerin kalıcı olarak silinir. Bu cihazdaki kayıtlar silinmez. Geri alınamaz.", do)

    async def accept_consent():
        workspace["consent_v1"] = date.today().isoformat()
        await save_workspace(preferences, workspace)
        if membership_client.signed_in:
            for kind in ("privacy", "terms"):
                try:
                    await membership_client.record_consent(kind)
                except MembershipApiError:
                    pass
        if not workspace.get("profile", {}).get("business_name"):
            business.show_profile(page, workspace.get("profile", {}), save_profile)

    async def membership_action(action, email, password):
        try:
            if action == "sign_up":
                result = await membership_client.sign_up(email, password)
                cloud_sync.attach_membership(membership_client)
            elif action == "sign_in":
                result = await membership_client.sign_in(email, password)
                cloud_sync.attach_membership(membership_client)
                if cloud_sync.session and premium_active():
                    await cloud_sync.sync_now()
                    result = f"{result} · {cloud_sync.state['message']}"
            elif action == "sign_out":
                await membership_client.sign_out()
                cloud_sync.detach()
                result = "Oturum kapatıldı. Bulut eşitlemesi durdu; kayıtlar cihazda."
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
            if kind in {"pos", "quote", "bank_import"} and not premium_active():
                require_premium("Banka CSV" if kind == "bank_import" else kind)
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

            if kind == "intake":
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
                        customer_record = {
                            "id": customer_id,
                            "name": customer_name,
                            "phone": "",
                            "balance": 0.0,
                            "due_date": values.get("due_date", "").strip() or default_due_date(),
                        }
                        records["customers"].append(customer_record)
                    customer_record["balance"] += amount
                    due = values.get("due_date", "").strip()
                    if due:
                        customer_record["due_date"] = due
                    elif not customer_record.get("due_date"):
                        customer_record["due_date"] = default_due_date()
                    transaction["title"] = f"Veresiye · {customer_record['name']} · {title}"
                    transaction["customer_id"] = customer_record["id"]
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
                records["transactions"].append({"id": _next_id(records["transactions"]), "type": entry_type, "title": title, "amount": amount, "date": date.today().isoformat()})
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
                    customer = {
                        "id": _next_id(records["customers"]),
                        "name": name,
                        "phone": "",
                        "balance": 0.0,
                        "due_date": default_due_date(),
                    }
                    records["customers"].append(customer)
                customer["balance"] += amount
                if not customer.get("due_date"):
                    customer["due_date"] = default_due_date()
                records["transactions"].append(
                    {
                        "id": _next_id(records["transactions"]),
                        "type": "debt",
                        "title": f"Veresiye · {customer['name']}",
                        "amount": amount,
                        "date": date.today().isoformat(),
                        "customer_id": customer["id"],
                    }
                )

            elif kind == "collect":
                amount = _number(values["amount"])
                if amount <= 0:
                    raise ValueError("Tahsilat tutarı sıfırdan büyük olmalı.")
                customer = next(c for c in records["customers"] if c["id"] == subject["id"])
                if amount > customer["balance"]:
                    raise ValueError("Tahsilat, müşterinin açık bakiyesinden fazla olamaz.")
                customer["balance"] -= amount
                records["cash_balance"] += amount
                records["transactions"].append({"id": _next_id(records["transactions"]), "type": "income", "title": f"Tahsilat · {customer['name']}", "amount": amount, "date": date.today().isoformat(), "customer_id": customer["id"], "collection": True})

            elif kind == "customer":
                name = values["name"].strip()
                if not name:
                    raise ValueError("Müşteri adını yaz.")
                if any(c["name"].casefold() == name.casefold() for c in records["customers"]):
                    raise ValueError("Bu müşteri zaten kayıtlı.")
                records["customers"].append({"id": _next_id(records["customers"]), "name": name, "phone": _normalize_phone(values["phone"]), "balance": 0.0})

            elif kind == "product":
                name = values["name"].strip()
                if not name:
                    raise ValueError("Ürün veya hizmet adını yaz.")
                qty = _integer(values["qty"] or "0")
                min_qty = _integer(values["min_qty"] or "0")
                price = _number(values["price"] or "0")
                if qty < 0 or min_qty < 0 or price < 0:
                    raise ValueError("Stok, uyarı seviyesi ve fiyat negatif olamaz.")
                barcode = values["barcode"].strip()
                if barcode and any(p.get("barcode") == barcode for p in records["products"]):
                    raise ValueError("Bu barkod başka bir üründe kayıtlı.")
                records["products"].append({"id": _next_id(records["products"]), "name": name, "barcode": barcode, "qty": qty, "min_qty": min_qty, "price": price})

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
                records["transactions"].append({"id": _next_id(records["transactions"]), "type": "income", "title": f"Satış · {product['name']} × {qty}", "amount": amount, "date": date.today().isoformat(), "product_id": product["id"], "qty": qty if product["min_qty"] > 0 else 0})

            elif kind == "pos":
                gross = _number(values["gross"])
                rate = _number(values["rate"])
                days = _integer(values["days"])
                if gross <= 0 or rate < 0 or rate > 100 or days < 0:
                    raise ValueError("Tutar pozitif olmalı; kesinti %0–100, gün sayısı sıfır veya daha büyük olmalı.")
                net = round(gross * (1 - rate / 100), 2)
                pos_id = _next_id(records["pos"])
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
                records["quotes"].append({"id": _next_id(records["quotes"]), "customer": customer, "title": title, "materials": materials, "labor": labor, "date": date.today().isoformat()})

            elif kind == "opening":
                amount = _number(values["amount"] or "0")
                if amount < 0:
                    raise ValueError("Kasa tutarı negatif olamaz.")
                records["cash_balance"] = amount

            elif kind == "bank_import":
                rows = values.get("rows") or []
                if not rows:
                    raise ValueError("CSV'de aktarılacak satır bulunamadı.")
                for row in rows:
                    month_key = str(row.get("date", date.today().isoformat()))[:7]
                    month_count = sum(1 for item in records["transactions"] if item.get("date", "").startswith(month_key))
                    if not ensure_basic_capacity("monthly_transactions", month_count):
                        return False
                    amount = float(row["amount"])
                    entry_type = row["type"]
                    records["transactions"].append(
                        {
                            "id": max((int(t.get("id", 0)) for t in records["transactions"]), default=0) + 1,
                            "type": entry_type,
                            "title": row["title"],
                            "amount": amount,
                            "date": row.get("date") or date.today().isoformat(),
                        }
                    )
                    records["cash_balance"] += amount if entry_type == "income" else -amount

            await persist()
            return True
        except (ValueError, StopIteration, KeyError) as error:
            set_status(str(error) or "Bilgileri kontrol edip tekrar dene.")
            return False

    def confirm(title, text, on_yes):
        async def yes(e):
            page.pop_dialog()
            await on_yes()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title, color=INK, weight=ft.FontWeight.BOLD),
                content=ft.Text(text, color=MUTED),
                actions=[
                    ft.TextButton(content="Vazgeç", on_click=lambda e: page.pop_dialog()),
                    ft.Button(content="Evet, sil", on_click=yes, bgcolor="#D64545", color=WHITE),
                ],
            )
        )

    def delete_transaction(item):
        async def do():
            target = next((t for t in records["transactions"] if t["id"] == item["id"]), None)
            if target is None:
                return
            amount = float(target.get("amount", 0))
            kind = target.get("type")
            customer = next((c for c in records["customers"] if c["id"] == target.get("customer_id")), None)
            if kind == "debt":
                if customer:
                    customer["balance"] = max(0.0, customer["balance"] - amount)
            elif kind == "income":
                records["cash_balance"] -= amount
                if target.get("collection") and customer:
                    customer["balance"] += amount
                product = next((p for p in records["products"] if p["id"] == target.get("product_id")), None)
                if product and target.get("qty"):
                    product["qty"] += int(target["qty"])
                pos = next((p for p in records["pos"] if p["id"] == target.get("pos_id")), None)
                if pos:
                    pos["paid"] = False
            else:
                records["cash_balance"] += amount
            records["transactions"] = [t for t in records["transactions"] if t["id"] != target["id"]]
            if evidence.pop(str(target["id"]), None) is not None:
                await save_evidence(preferences, evidence)
            await persist("Kayıt silindi, kasa ve bakiyeler düzeltildi.")

        confirm("Kayıt silinsin mi?", f"{item['title']} · {item['amount']:.2f} TL silinir; kasa ve müşteri bakiyesi geri düzeltilir.", do)

    def delete_customer(item):
        async def do():
            records["customers"] = [c for c in records["customers"] if c["id"] != item["id"]]
            await persist("Müşteri silindi. Geçmiş hareketler defterde kalır.")

        warn = f" Açık bakiyesi {item['balance']:.2f} TL." if item.get("balance", 0) > 0 else ""
        confirm("Müşteri silinsin mi?", f"{item['name']} silinecek.{warn}", do)

    def delete_product(item):
        async def do():
            records["products"] = [p for p in records["products"] if p["id"] != item["id"]]
            await persist("Kalem silindi.")

        confirm("Kalem silinsin mi?", f"{item['name']} silinecek.", do)

    async def mark_pos(item):
        if not require_premium("POS takibi"):
            return
        pos = next((p for p in records["pos"] if p["id"] == item["id"]), None)
        if pos is None:
            return
        pos["paid"] = not pos["paid"]
        if pos["paid"]:
            records["cash_balance"] += pos["net"]
            records["transactions"].append({"id": _next_id(records["transactions"]), "type": "income", "title": f"POS'tan geldi · {pos['bank']}", "amount": pos["net"], "date": date.today().isoformat(), "pos_id": pos["id"]})
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

    async def export_statement(customer):
        profile = workspace.get("profile", {})
        pdf = customer_statement_pdf(customer, records, profile)
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in customer.get("name", "musteri"))[:40]
        await save_file(f"nakitce_ekstre_{safe_name}.pdf", pdf)

    async def send_reminder(customer):
        profile = workspace.get("profile", {})
        message = whatsapp_reminder_message(customer, profile)
        pdf = customer_statement_pdf(customer, records, profile)
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in customer.get("name", "musteri"))[:40]
        file_name = f"nakitce_ekstre_{safe_name}.pdf"
        try:
            await share.share_files(
                [ft.ShareFile(data=pdf, name=file_name, mime_type="application/pdf")],
                text=message,
                title="Nakitçe hesap ekstresi",
                subject="Hesap ekstresi",
            )
            set_status("PDF ekstre paylaşıma hazır. WhatsApp'ı seçip göndermeden önce kontrol et.")
            show_snack("Ekstre paylaşıldı · WhatsApp'ı seçebilirsin")
        except Exception as error:
            log.warning("Share sheet failed: %s", error)
            phone = "".join(char for char in customer.get("phone", "") if char.isdigit())
            try:
                await save_file(file_name, pdf)
                if phone:
                    await url_launcher.launch_url(f"https://wa.me/{phone}?text={quote(message)}")
                    set_status("PDF kaydedildi ve WhatsApp mesajı açıldı. Ekstreyi sohbete ekleyebilirsin.")
                else:
                    set_status("PDF kaydedildi. Müşteri telefonu yok; WhatsApp için numara ekle.")
            except Exception as inner:
                log.warning("WhatsApp fallback failed: %s", inner)
                set_status("Paylaşım açılamadı. Telefon ve depolama izinlerini kontrol et.")

    async def copy_gib_draft():
        profile = workspace.get("profile", {})
        draft = "\n".join(
            [
                "Nakitçe · GİB e-Arşiv hazırlık notu",
                f"İşletme: {profile.get('business_name', '')}",
                f"Yetkili: {profile.get('owner', '')}",
                f"Vergi dairesi: {profile.get('tax_office', '')}",
                f"VKN / TCKN: {profile.get('tax_number', '')}",
                f"Adres: {profile.get('address', '')}",
                f"Telefon: {profile.get('phone', '')}",
                "",
                "Not: Bu metin portal formu için kopyalandı. Fatura GİB'de kesilir; Nakitçe şifre istemez.",
            ]
        )
        try:
            await clipboard.set(draft)
            set_status("GİB hazırlık metni panoya kopyalandı.")
            show_snack("Panoya kopyalandı · GİB portalını açabilirsin")
        except Exception as error:
            log.warning("Clipboard failed: %s", error)
            set_status("Panoya kopyalanamadı.")

    async def import_bank_csv():
        if not require_premium("Banka CSV içe aktarma"):
            return
        try:
            picked = await file_picker.pick_files(
                dialog_title="Banka CSV seç",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["csv", "txt"],
                allow_multiple=False,
                with_data=True,
            )
            if not picked:
                set_status("CSV seçimi iptal edildi.")
                return
            rows = parse_bank_csv(picked[0].bytes or b"")
            if not rows:
                set_status("CSV okunamadı veya satır bulunamadı. Tarih/tutar sütunlarını kontrol et.")
                return
            ok = await process_form("bank_import", {"rows": rows}, None)
            if ok:
                show_snack(f"{len(rows)} banka hareketi aktarıldı")
                set_status(f"{len(rows)} satır kasaya işlendi. Tutarları kontrol et.")
        except Exception as error:
            log.exception("Bank import failed")
            set_status(f"CSV aktarılamadı: {error}")

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
        profile = workspace.get("profile", {})
        await save_file("nakitce_teklif.pdf", quote_pdf(quote_record, profile))

    async def export_pdf():
        period = date.today().strftime("%Y_%m")
        await save_file(
            f"nakitce_{period}_isletme_raporu.pdf",
            business_report_pdf(records, workspace.get("profile", {})),
        )

    async def export_csv():
        period = date.today().strftime("%Y_%m")
        await save_file(f"nakitce_{period}_isletme_raporu.csv", csv_report(records, workspace.get("profile", {})))

    async def purchase_premium():
        if not billing.available:
            set_status("Play Billing bu derlemede yok. Çalışmayan satın alma gösterilmez.")
            return
        if not membership_client.signed_in:
            set_status("Önce Nakitçe hesabına giriş yap.")
            open_membership()
            return
        token = await billing.launch_purchase(PRODUCT_MONTHLY)
        if not token:
            set_status("Satın alma başlatılamadı.")
            return
        try:
            await membership_client.verify_play_purchase(token, PRODUCT_MONTHLY)
            set_status("Satın alma sunucuda doğrulandı.")
            show_snack("Premium açıldı")
        except MembershipApiError as error:
            set_status(str(error))
        refresh()

    def start_pos_toggle(item):
        if require_premium("POS takibi"):
            asyncio.create_task(mark_pos(item))

    def start_reminder(customer):
        asyncio.create_task(send_reminder(customer))

    def start_statement(customer):
        asyncio.create_task(export_statement(customer))

    def start_quote_pdf(item):
        asyncio.create_task(export_quote(item))

    def start_csv():
        asyncio.create_task(export_csv())

    def start_pdf():
        asyncio.create_task(export_pdf())

    def start_cloud_sync():
        cloud_sync.attach_membership(membership_client)
        if not cloud_sync.session:
            set_status("Bulut için Nakitçe hesabına giriş yap. Kendi Supabase açmana gerek yok.")
            open_membership()
            return
        if not require_premium("Bulut eşitleme"):
            return
        asyncio.create_task(sync_and_refresh())

    actions = {
        "income": lambda e: show("income"),
        "expense": lambda e: show("expense"),
        "debt": lambda e: show("debt"),
        "intake": lambda e: show("intake"),
        "sale": lambda e: select_tab("inventory"),
        "add": lambda e: show("customer"),
        "collect": lambda customer: show("collect", customer),
        "remind": start_reminder,
        "statement_pdf": start_statement,
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
        "gib_draft": lambda e: asyncio.create_task(copy_gib_draft()),
        "import_bank": lambda e: asyncio.create_task(import_bank_csv()),
        "evidence": show_evidence,
        "sync_setup": lambda e: open_membership(),
        "sync_now": lambda e: start_cloud_sync(),
        "sync_upload": lambda e: asyncio.create_task(resolve_and_refresh("upload")) if require_premium("Bulut eşitleme") else None,
        "sync_download": lambda e: asyncio.create_task(resolve_and_refresh("download")) if require_premium("Bulut eşitleme") else None,
        "edit_profile": lambda e: open_profile(),
        "membership": lambda e: open_membership(),
        "add_reminder": lambda e: open_reminder(),
        "opening": lambda e: show("opening"),
        "legal": lambda e: open_legal(),
        "delete_transaction": delete_transaction,
        "delete_customer": delete_customer,
        "delete_product": delete_product,
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
        padding=ft.Padding.only(left=16, right=16, top=16, bottom=10),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#FFFFFF", "#E8F7F2"],
        ),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Image(
                    src="icon.png",
                    width=44,
                    height=44,
                    fit=ft.BoxFit.CONTAIN,
                    semantics_label="Nakitçe",
                ),
                ft.Column(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Text("Nakitçe", size=22, weight=ft.FontWeight.BOLD, color=INK),
                        ft.Text("Ticaretin kalbi", size=11, color=MUTED, weight=ft.FontWeight.W_600),
                    ],
                ),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    border_radius=999,
                    bgcolor="#E8F7F2",
                    content=ft.Text("Cebindeki kasa", color=TEAL, size=11, weight=ft.FontWeight.W_700),
                ),
            ],
        ),
    )
    status_bar = ft.Container(padding=ft.Padding.symmetric(horizontal=18, vertical=5), content=status_text)
    root = ft.Column(expand=True, spacing=0, controls=[header, status_bar, content, nav])
    page.add(root)
    if seed_tax_reminders(workspace):
        await save_workspace(preferences, workspace)
    refresh()
    alerts = critical_alerts(records, workspace)
    if alerts:
        top = alerts[0]
        snack_bg = "#FFF1D8" if top["tone"] == "amber" else ("#D64545" if top["tone"] == "red" else TEAL)
        show_snack(f"{top['title']} — {top['subtitle'][:60]}", color=snack_bg)
    if not workspace.get("consent_v1"):
        business.show_consent(page, accept_consent)
    elif not workspace.get("profile", {}).get("business_name"):
        business.show_profile(page, workspace.get("profile", {}), save_profile)

    asyncio.create_task(cloud_sync.retry_loop())
    log.info("Nakitçe opened with %d customers and %d transactions", len(records["customers"]), len(records["transactions"]))


ft.run(main)
