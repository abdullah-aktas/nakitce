import httpx


class SupabaseError(Exception):
    pass


class SupabaseClient:
    def __init__(self, project_url, anon_key):
        self.base_url = project_url.rstrip("/")
        self.anon_key = anon_key.strip()

    def _headers(self, access_token=None):
        headers = {"apikey": self.anon_key, "Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def sign_in(self, email, password):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/auth/v1/token?grant_type=password",
                headers=self._headers(),
                json={"email": email, "password": password},
            )
        if response.status_code >= 400:
            raise SupabaseError("Giriş başarısız. E-posta ve parolayı kontrol et.")
        return response.json()

    async def refresh(self, refresh_token):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/auth/v1/token?grant_type=refresh_token",
                headers=self._headers(),
                json={"refresh_token": refresh_token},
            )
        if response.status_code >= 400:
            raise SupabaseError("Oturum yenilenemedi. Bulut hesabına yeniden giriş yap.")
        return response.json()

    async def get_snapshot(self, user_id, access_token):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.base_url}/rest/v1/nakitce_snapshots",
                headers=self._headers(access_token),
                params={
                    "select": "user_id,records,updated_at",
                    "user_id": f"eq.{user_id}",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError("Bulut kaydı okunamadı. Supabase tablosu ve RLS ayarlarını kontrol et.")
        rows = response.json()
        return rows[0] if rows else None

    async def save_snapshot(self, user_id, records, updated_at, access_token):
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/rest/v1/nakitce_snapshots?on_conflict=user_id",
                headers={
                    **self._headers(access_token),
                    "Prefer": "resolution=merge-duplicates,return=representation",
                },
                json={"user_id": user_id, "records": records, "updated_at": updated_at},
            )
        if response.status_code >= 400:
            raise SupabaseError("Buluta kayıt yapılamadı. Tablo ve kullanıcı yetkilerini kontrol et.")
        rows = response.json()
        if not rows:
            raise SupabaseError("Supabase kayıt yanıtı boş döndü.")
        return rows[0]
