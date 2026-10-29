"""Client for account authentication and server-owned Premium entitlements."""

import json
import logging

import httpx

from membership import as_cached_status, premium_access, stamp_cache
from membership_config import MEMBERSHIP_SUPABASE_ANON_KEY, MEMBERSHIP_SUPABASE_URL

log = logging.getLogger("app.membership_api")
_SESSION_KEY = "nakitce_membership_session_v1"
_STATUS_CACHE_KEY = "nakitce_membership_status_cache_v1"
_LEGACY_SESSION_KEYS = ("tikir_membership_session_v1",)


class MembershipApiError(Exception):
    pass


class MembershipClient:
    def __init__(self, preferences):
        self.preferences = preferences
        self.base_url = MEMBERSHIP_SUPABASE_URL.strip().rstrip("/")
        self.anon_key = MEMBERSHIP_SUPABASE_ANON_KEY.strip()
        self.session = {}
        self.status = None
        self.message = "Hesap üyeliği için bağlantı gerekli."

    @property
    def configured(self):
        return self.base_url.startswith("https://") and bool(self.anon_key)

    @property
    def signed_in(self):
        return bool(self.session.get("access_token"))

    def _headers(self, access_token=None):
        headers = {"apikey": self.anon_key, "Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def initialize(self):
        raw = await self.preferences.get(_SESSION_KEY)
        if not raw:
            for legacy in _LEGACY_SESSION_KEYS:
                raw = await self.preferences.get(legacy)
                if raw:
                    break
        if raw:
            try:
                self.session = json.loads(raw)
            except (TypeError, ValueError):
                self.session = {}
        await self._load_status_cache()
        if not self.configured:
            self.message = "Üyelik sunucusu henüz yapılandırılmadı; Premium kapalı."
            if not premium_access(self.status, allow_cache=True):
                self.status = None
            return
        if self.signed_in:
            try:
                await self.refresh_status()
            except MembershipApiError as error:
                log.info("Membership status unavailable at startup: %s", error)
                self.message = str(error)
                if not premium_access(self.status, allow_cache=True):
                    self.status = None

    async def _load_status_cache(self):
        raw = await self.preferences.get(_STATUS_CACHE_KEY)
        if not raw:
            return
        try:
            stored = json.loads(raw)
        except (TypeError, ValueError):
            return
        cached = as_cached_status(stored)
        if premium_access(cached, allow_cache=True):
            self.status = cached
            self.message = "Son doğrulanmış üyelik önbellekten gösteriliyor (çevrimdışı)."

    async def _persist_session(self):
        if self.session:
            await self.preferences.set(_SESSION_KEY, json.dumps(self.session, ensure_ascii=False))
        else:
            await self.preferences.remove(_SESSION_KEY)

    async def _persist_status_cache(self):
        stamped = stamp_cache(self.status)
        if stamped:
            await self.preferences.set(_STATUS_CACHE_KEY, json.dumps(stamped, ensure_ascii=False))
        else:
            await self.preferences.remove(_STATUS_CACHE_KEY)

    async def _auth_request(self, path, body):
        if not self.configured:
            raise MembershipApiError("Üyelik sunucusu yapılandırılmadı.")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/auth/v1/{path}",
                headers=self._headers(),
                json=body,
            )
        if response.status_code >= 400:
            try:
                detail = response.json().get("msg") or response.json().get("message")
            except Exception:
                detail = None
            raise MembershipApiError(detail or "Hesap işlemi tamamlanamadı. Bilgileri kontrol edip yeniden dene.")
        return response.json()

    async def sign_up(self, email, password):
        if len(password) < 8:
            raise MembershipApiError("Parola en az 8 karakter olmalı.")
        result = await self._auth_request(
            "signup",
            {"email": email.strip(), "password": password},
        )
        if result.get("access_token"):
            self.session = result
            await self._persist_session()
            await self.refresh_status()
            return "Hesap açıldı ve oturum başladı."
        self.message = "Hesap açıldı. E-postandaki doğrulama bağlantısına tıklayıp giriş yap."
        return self.message

    async def sign_in(self, email, password):
        result = await self._auth_request(
            "token?grant_type=password",
            {"email": email.strip(), "password": password},
        )
        self.session = result
        await self._persist_session()
        await self.refresh_status()
        return "Giriş yapıldı; üyelik sunucudan doğrulandı."

    async def sign_out(self):
        self.session = {}
        self.status = None
        self.message = "Oturum kapatıldı."
        await self._persist_session()
        await self.preferences.remove(_STATUS_CACHE_KEY)

    async def _refresh_session(self):
        refresh_token = self.session.get("refresh_token")
        if not refresh_token:
            raise MembershipApiError("Oturum sona erdi. Yeniden giriş yap.")
        result = await self._auth_request(
            "token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )
        self.session = result
        await self._persist_session()

    async def _function_call(self, payload):
        if not self.configured:
            raise MembershipApiError("Üyelik sunucusu yapılandırılmadı.")
        if not self.signed_in:
            raise MembershipApiError("Önce Nakitçe hesabına giriş yap.")
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                f"{self.base_url}/functions/v1/membership",
                headers=self._headers(self.session["access_token"]),
                json=payload,
            )
        if response.status_code in {401, 403}:
            await self._refresh_session()
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    f"{self.base_url}/functions/v1/membership",
                    headers=self._headers(self.session["access_token"]),
                    json=payload,
                )
        if response.status_code >= 400:
            try:
                detail = response.json().get("error")
            except Exception:
                detail = None
            raise MembershipApiError(detail or "Üyelik sunucusundan yanıt alınamadı.")
        return response.json()

    async def refresh_status(self):
        result = await self._function_call({"action": "status"})
        if result.get("server_verified") is not True:
            raise MembershipApiError("Sunucu üyeliği doğrulanamadı; Premium özellikler kapalı.")
        result = dict(result)
        result["from_cache"] = False
        self.status = result
        self.message = result.get("message", "Üyelik durumu sunucudan doğrulandı.")
        await self._persist_status_cache()
        return result

    async def verify_play_purchase(self, purchase_token, product_id=None):
        if not purchase_token:
            raise MembershipApiError("Google Play satın alma belirteci alınamadı.")
        payload = {"action": "verify_play_purchase", "purchase_token": purchase_token}
        if product_id:
            payload["product_id"] = product_id
        result = await self._function_call(payload)
        if result.get("server_verified") is not True:
            raise MembershipApiError("Google Play satın alması sunucuda doğrulanamadı.")
        result = dict(result)
        result["from_cache"] = False
        self.status = result
        self.message = result.get("message", "Google Play üyeliği doğrulandı.")
        await self._persist_status_cache()
        return result

    async def redeem_code(self, code):
        result = await self._function_call({"action": "redeem_code", "code": code})
        result = dict(result)
        result['from_cache'] = False
        self.status = result
        self.message = result.get('message', 'Kod uygulandı.')
        await self._persist_status_cache()
        return self.message

    async def record_consent(self, kind, accepted=True, version='1'):
        await self._function_call({"action": "record_consent", "kind": kind, "accepted": accepted, "version": version})

    async def delete_account(self):
        await self._function_call({"action": "delete_account", "confirm": "SIL"})
        await self.sign_out()
