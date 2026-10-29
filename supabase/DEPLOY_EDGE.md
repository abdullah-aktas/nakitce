# Edge Function: membership — adım adım

## Yöntem A · Komut satırı (önerilen)

### 1) Supabase CLI kur

PowerShell’de:

```powershell
npm install -g supabase
```

Kurulum sorarsa Node.js gerekir: https://nodejs.org

### 2) Giriş yap

```powershell
supabase login
```

Tarayıcı açılır → Supabase hesabınla onayla.

### 3) Projeyi bağla

```powershell
cd "d:\Mobil App\Nakitçe"
supabase link --project-ref cdxyxohetqwfwnozhjxw
```

Database şifresi sorarsa Dashboard → **Project Settings → Database** içindeki şifreyi kullan  
(yoksa “Reset database password” ile yeni oluştur).

### 4) Fonksiyonu yayınla

```powershell
supabase functions deploy membership --no-verify-jwt=false
```

Başarılı olunca Dashboard → **Edge Functions** altında `membership` görünür.

### 5) (Gerekirse) secrets

Çoğu projede `SUPABASE_URL` ve `SUPABASE_SERVICE_ROLE_KEY` otomatik gelir.  
Eksikse:

```powershell
supabase secrets set SUPABASE_ANON_KEY="BURAYA_ANON_VEYA_PUBLISHABLE_KEY"
```

Service role’ü Dashboard → **Project Settings → API** → `service_role` (gizli) ile kopyala; CLI deploy sırasında genelde otomatik enjekte edilir.

---

## Yöntem B · Dashboard editörü

1. Aç: https://supabase.com/dashboard/project/cdxyxohetqwfwnozhjxw/functions  
2. **Deploy a new function** / **Create function**  
3. İsim: `membership`  
4. `d:\Mobil App\Nakitçe\supabase\functions\membership\index.ts` dosyasının **tüm** kodunu yapıştır  
5. Deploy / Save  

JWT doğrulama: **açık** kalsın (`verify_jwt`).

---

## Test

Uygulamada **Üyelik** → hesap oluştur / giriş yap.  
Hata olursa Edge Functions → `membership` → Logs sekmesine bak.
