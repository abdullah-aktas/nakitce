"""Bulut eşitleme · yalnızca Miras Nakitçe Supabase projesi.

Kullanıcı kendi proje URL/key girmez. Oturum = Nakitçe üyelik hesabı (aynı Auth).
"""

import asyncio
import logging
from datetime import datetime, timezone

from membership_config import MEMBERSHIP_SUPABASE_ANON_KEY, MEMBERSHIP_SUPABASE_URL
from storage import load_sync_meta, save_records, save_sync_meta
from supabase_api import SupabaseClient, SupabaseError

log = logging.getLogger("app.cloud_sync")

_RECORD_KEYS = ("customers", "transactions", "products", "pos", "quotes", "cash_balance", "notice")


class CloudSync:
    def __init__(self, preferences, records, workspace=None):
        self.preferences = preferences
        self.records = records
        self.workspace = workspace if workspace is not None else {"profile": {}, "mode": "simple", "reminders": []}
        self.meta = {}
        self.session = {}
        self.client = None
        self.state = {
            "message": self._idle_message(),
            "conflict": False,
            "remote_snapshot": None,
            "hosted": True,
        }

    @staticmethod
    def _idle_message():
        if not (MEMBERSHIP_SUPABASE_URL.strip().startswith("https://") and MEMBERSHIP_SUPABASE_ANON_KEY.strip()):
            return "Bulut henüz yapılandırılmadı (geliştirici: membership_config + supabase/)."
        return "Bulut için Nakitçe hesabına giriş yap."

    @property
    def configured(self):
        return MEMBERSHIP_SUPABASE_URL.strip().startswith("https://") and bool(MEMBERSHIP_SUPABASE_ANON_KEY.strip())

    def _payload(self):
        payload = {key: self.records.get(key) for key in _RECORD_KEYS if key in self.records}
        payload["workspace"] = {
            "profile": self.workspace.get("profile", {}),
            "mode": self.workspace.get("mode", "simple"),
            "reminders": self.workspace.get("reminders", []),
        }
        return payload

    async def initialize(self):
        self.meta = await load_sync_meta(self.preferences)
        if "local_updated_at" not in self.meta:
            self.meta["local_updated_at"] = self._now()
            await self.save_meta()
        self.state["message"] = self._idle_message()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    async def save_meta(self):
        await save_sync_meta(self.preferences, self.meta)

    def mark_local_change(self):
        self.meta["local_updated_at"] = self._now()

    def attach_membership(self, membership_client):
        """Nakitçe oturumunu buluta bağla — kullanıcı proje bilgisi girmez."""
        if not self.configured:
            self.client = None
            self.session.clear()
            self.state["message"] = self._idle_message()
            return False
        if not membership_client or not membership_client.signed_in:
            self.client = None
            self.session.clear()
            self.state["message"] = "Bulut için Nakitçe hesabına giriş yap."
            return False

        auth = membership_client.session
        user = auth.get("user") or {}
        user_id = user.get("id") or auth.get("user_id")
        if not user_id:
            self.state["message"] = "Oturumda kullanıcı kimliği yok. Yeniden giriş yap."
            return False

        self.client = SupabaseClient(MEMBERSHIP_SUPABASE_URL.strip().rstrip("/"), MEMBERSHIP_SUPABASE_ANON_KEY.strip())
        self.session = {
            "access_token": auth.get("access_token"),
            "refresh_token": auth.get("refresh_token"),
            "expires_in": auth.get("expires_in", 3600),
            "user": user,
            "user_id": user_id,
            "expires_at": datetime.now(timezone.utc).timestamp() + auth.get("expires_in", 3600),
        }
        email = user.get("email") or ""
        if self.meta.get("user_id") != user_id:
            self.meta = {"user_id": user_id, "local_updated_at": self._now()}
        self.state["message"] = f"Nakitçe bulutu hazır · {email}" if email else "Nakitçe bulutu hazır."
        return True

    def detach(self):
        self.client = None
        self.session.clear()
        self.state.update(conflict=False, remote_snapshot=None, message=self._idle_message())

    async def connect(self, values=None):
        """Eski BYO-Supabase yolu kapalı — yalnızca bilgi mesajı."""
        raise ValueError(
            "Kendi Supabase projeni bağlaman gerekmez. "
            "Üyelik ekranından Nakitçe hesabına giriş yap; bulut otomatik açılır."
        )

    async def _ensure_session(self):
        if self.client is None or not self.session.get("access_token"):
            return False
        now = datetime.now(timezone.utc).timestamp()
        if now >= self.session.get("expires_at", 0) - 60:
            refresh = self.session.get("refresh_token")
            if not refresh:
                return False
            renewed = await self.client.refresh(refresh)
            self.session.update(renewed)
            user = renewed.get("user") or self.session.get("user") or {}
            self.session["user"] = user
            self.session["user_id"] = user.get("id") or self.session.get("user_id")
            self.session["expires_at"] = now + renewed.get("expires_in", 3600)
        return bool(self.session.get("user_id") and self.session.get("access_token"))

    async def _upload(self):
        remote = await self.client.save_snapshot(
            self.session["user_id"], self._payload(), self._now(), self.session["access_token"]
        )
        self.meta["base_local_updated_at"] = self.meta["local_updated_at"]
        self.meta["base_remote_updated_at"] = remote["updated_at"]
        await self.save_meta()
        self.state.update(
            conflict=False,
            remote_snapshot=None,
            message="Nakitçe bulutuyla eşitlendi.",
        )

    async def _download(self, remote):
        from storage import save_workspace

        cloud_records = remote.get("records")
        if not isinstance(cloud_records, dict):
            raise SupabaseError("Bulut kaydı okunamadı; kayıt biçimi geçersiz.")
        payload = dict(cloud_records)
        remote_workspace = payload.pop("workspace", None)
        self.records.clear()
        for key in _RECORD_KEYS:
            if key in payload:
                self.records[key] = payload[key]
        self.records.setdefault("customers", [])
        self.records.setdefault("transactions", [])
        self.records.setdefault("products", [])
        self.records.setdefault("pos", [])
        self.records.setdefault("quotes", [])
        self.records.setdefault("cash_balance", 0.0)
        self.records.setdefault("notice", "Buluttan alındı.")
        await save_records(self.preferences, self.records)
        if isinstance(remote_workspace, dict):
            self.workspace.clear()
            self.workspace.update(
                {
                    "profile": remote_workspace.get("profile") or {},
                    "mode": remote_workspace.get("mode") or "simple",
                    "reminders": remote_workspace.get("reminders") or [],
                }
            )
            await save_workspace(self.preferences, self.workspace)
        self.meta["local_updated_at"] = remote["updated_at"]
        self.meta["base_local_updated_at"] = remote["updated_at"]
        self.meta["base_remote_updated_at"] = remote["updated_at"]
        await self.save_meta()
        self.state.update(
            conflict=False,
            remote_snapshot=None,
            message="Buluttaki kayıtlar bu cihaza alındı.",
        )

    async def sync_now(self):
        try:
            if not await self._ensure_session():
                self.state["message"] = "Bulut için Nakitçe hesabına giriş yap. Kendi Supabase açmana gerek yok."
                return
            remote = await self.client.get_snapshot(self.session["user_id"], self.session["access_token"])
            base_remote = self.meta.get("base_remote_updated_at")
            base_local = self.meta.get("base_local_updated_at")
            if not base_remote:
                if remote is None:
                    await self._upload()
                else:
                    self.state.update(
                        conflict=True,
                        remote_snapshot=remote,
                        message="Bu hesapta bulutta kayıt var. İlk eşitlemede cihaz veya bulut kopyasını seç.",
                    )
            elif remote is None:
                await self._upload()
            else:
                local_changed = self.meta.get("local_updated_at") != base_local
                remote_changed = remote.get("updated_at") != base_remote
                if local_changed and remote_changed:
                    self.state.update(
                        conflict=True,
                        remote_snapshot=remote,
                        message="Cihaz ve bulut ayrı ayrı değişmiş; hangi kopyanın kalacağını seç.",
                    )
                elif local_changed:
                    await self._upload()
                elif remote_changed:
                    await self._download(remote)
                else:
                    self.state["message"] = "Nakitçe bulutu güncel."
        except Exception as error:
            log.warning("Cloud sync deferred: %s", error)
            self.state["message"] = "Buluta ulaşılamadı. Kayıtlar cihazda güvende; bağlantı gelince yeniden denenecek."

    async def resolve(self, choice):
        if not await self._ensure_session():
            return
        remote = self.state.get("remote_snapshot")
        if choice == "download":
            if remote is None:
                remote = await self.client.get_snapshot(self.session["user_id"], self.session["access_token"])
            if remote is None:
                await self._upload()
            else:
                await self._download(remote)
        else:
            await self._upload()

    async def retry_loop(self):
        while True:
            await asyncio.sleep(45)
            if self.session and not self.state.get("conflict"):
                await self.sync_now()
