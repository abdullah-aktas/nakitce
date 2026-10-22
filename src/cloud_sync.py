import asyncio
import logging
from datetime import datetime, timezone

from storage import load_sync_config, load_sync_meta, save_records, save_sync_config, save_sync_meta
from supabase_api import SupabaseClient, SupabaseError

log = logging.getLogger("app.cloud_sync")


class CloudSync:
    def __init__(self, preferences, records):
        self.preferences = preferences
        self.records = records
        self.config = {}
        self.meta = {}
        self.session = {}
        self.client = None
        self.state = {
            "message": "Supabase bağlantısı ayarlanmadı.",
            "conflict": False,
            "remote_snapshot": None,
        }

    async def initialize(self):
        self.config = await load_sync_config(self.preferences)
        self.meta = await load_sync_meta(self.preferences)
        if "local_updated_at" not in self.meta:
            self.meta["local_updated_at"] = self._now()
            await self.save_meta()
        if self.config:
            self.state["message"] = "Supabase ayarları kayıtlı. Bulut eşitlemesi için hesabına yeniden giriş yap."

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    async def save_meta(self):
        await save_sync_meta(self.preferences, self.meta)

    def mark_local_change(self):
        self.meta["local_updated_at"] = self._now()

    async def connect(self, values):
        project_url = values["project_url"].strip().rstrip("/")
        anon_key = values["anon_key"].strip()
        email = values["email"].strip()
        password = values["password"]
        if not project_url.startswith("https://") or not anon_key or not email or not password:
            raise ValueError("HTTPS proje adresi, public key, e-posta ve parola gerekli.")

        client = SupabaseClient(project_url, anon_key)
        try:
            auth = await client.sign_in(email, password)
        except Exception as error:
            raise ValueError(f"Supabase bağlantısı kurulamadı: {error}") from error

        user_id = auth.get("user", {}).get("id")
        if not user_id:
            raise ValueError("Supabase oturumunda kullanıcı kimliği bulunamadı.")
        self.client = client
        self.session.clear()
        self.session.update(auth)
        self.session["user_id"] = user_id
        self.session["expires_at"] = datetime.now(timezone.utc).timestamp() + auth.get("expires_in", 3600)
        self.config = {"project_url": project_url, "anon_key": anon_key, "email": email}
        await save_sync_config(self.preferences, self.config)

        if self.meta.get("user_id") != user_id:
            self.meta = {"user_id": user_id, "local_updated_at": self._now()}
        await self.save_meta()
        self.state["message"] = f"Supabase hesabına bağlanıldı: {email}"
        await self.sync_now()

    async def _ensure_session(self):
        if self.client is None or not self.session:
            return False
        now = datetime.now(timezone.utc).timestamp()
        if now >= self.session.get("expires_at", 0) - 60:
            renewed = await self.client.refresh(self.session["refresh_token"])
            self.session.update(renewed)
            self.session["expires_at"] = now + renewed.get("expires_in", 3600)
        return True

    async def _upload(self):
        remote = await self.client.save_snapshot(
            self.session["user_id"], self.records, self._now(), self.session["access_token"]
        )
        self.meta["base_local_updated_at"] = self.meta["local_updated_at"]
        self.meta["base_remote_updated_at"] = remote["updated_at"]
        await self.save_meta()
        self.state.update(
            conflict=False,
            remote_snapshot=None,
            message="Bulutla eşitlendi · bu cihaz ve Supabase güncel.",
        )

    async def _download(self, remote):
        cloud_records = remote.get("records")
        if not isinstance(cloud_records, dict):
            raise SupabaseError("Bulut kaydı okunamadı; kayıt biçimi geçersiz.")
        self.records.clear()
        self.records.update(cloud_records)
        await save_records(self.preferences, self.records)
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
                self.state["message"] = "Önce Supabase hesabını bağla; çevrimdışı kayıtlar cihazda kalır."
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
                        message="Bu Supabase hesabında daha önce kayıt var. İlk eşitleme için cihaz veya bulut kopyasını seç.",
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
                        message="Cihaz ve bulut ayrı ayrı değişmiş; veri kaybını önlemek için seçim gerekiyor.",
                    )
                elif local_changed:
                    await self._upload()
                elif remote_changed:
                    await self._download(remote)
                else:
                    self.state["message"] = "Bulutla eşitlendi · tüm kayıtlar güncel."
        except Exception as error:
            log.warning("Cloud sync deferred: %s", error)
            self.state["message"] = "İnternet yok veya Supabase'e ulaşılamadı. Kayıtlar cihazda güvende; bağlantı gelince yeniden denenecek."

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
