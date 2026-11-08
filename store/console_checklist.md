# Nakitçe — Play Console yayın kontrol listesi

Package ID (org + proje): `com.mirasteknoloji.nakitce`  
Sürüm adı: `1.0.0` · build number: `2` (her yüklemede artır)

## A. Bu depoda hazır

- [x] Marka: Nakitçe, logo/ikon/özellik grafiği
- [x] Mağaza metni: `store/listing_tr.txt`
- [x] Veri güvenliği taslağı: `store/data_safety_tr.md`
- [x] Gizlilik politikası: `docs/privacy.html` (+ `PRIVACY_POLICY_TR.md`)
- [x] Android izinleri: `pyproject.toml` (INTERNET + CAMERA)
- [x] AAB derleme betiği: `scripts/build_play_aab.ps1`
- [x] Raster grafikler: `store/assets/icon_512.png`, `store/assets/play_feature_graphic.png`
- [x] Telefon ekran görüntüleri: `store/assets/screenshots/` (5 adet, 1080×1920)
- [x] İlk açılış demosu: boş başlangıç + “Örnekle dene” (`src/demo_seed.py`)
- [x] AAB üretildi: `build/aab/nakitce.aab` (~89 MB) — **şu an debug imzalı** olabilir

## B. Senin sıradaki adımların

1. **Upload keystore** oluştur ve güvenli yedekle (git’e koyma):
   ```powershell
   keytool -genkey -v -keystore $env:USERPROFILE\nakitce-upload.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias upload
   ```
2. **İmzalı AAB** üret:
   ```powershell
   $env:FLET_ANDROID_SIGNING_KEY_STORE="$env:USERPROFILE\nakitce-upload.jks"
   $env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD="..."
   $env:FLET_ANDROID_SIGNING_KEY_PASSWORD="..."
   $env:FLET_ANDROID_SIGNING_KEY_ALIAS="upload"
   .\scripts\build_play_aab.ps1
   ```
3. **Gizlilik URL’si** — GitHub Pages: Settings → Pages → `main` / `/docs` → `https://abdullah-aktas.github.io/nakitce/privacy.html`
4. **Play Console** — uygulama oluştur (ad: Nakitçe).
5. **Dahili test** — imzalı `build\aab\nakitce.aab` yükle; paket ID’yi doğrula.
6. **Mağaza listesi** — `store/listing_tr.txt` + `store/assets/*` + `store/assets/screenshots/*` (isteğe bağlı gerçek cihaz ekle).
7. **Veri güvenliği** — `store/data_safety_tr.md`.
8. **İçerik derecelendirmesi** — iş uygulaması / çocuklara yönelik değil.
9. **Premium açılacaksa (şimdilik üretimde açma)**  
   - Supabase üyelik + Edge Function  
   - `membership_config.py`  
   - Play ürünleri: `nakitce_premium_monthly` / `nakitce_premium_yearly`  
   - Billing köprüsü
10. **Üretim** — dahili test geçtikten sonra.

## C. Derleme notu (bu PC)

Kullanıcı adında boşluk olduğu için başarılı derleme şöyle yapıldı:

- `C:\AndroidSdk` → Android SDK junction  
- `C:\fh` → kullanıcı profili junction  
- `scripts\build_play_aab.ps1` bunları otomatik kullanır  

## D. Şimdilik üretime sürmeyin

- Debug imzalı AAB Play’e yüklenemez; upload keystore ile yeniden derleyin.
- Play Billing stub; aboneliği “çalışıyor” diye tanıtmayın.
- `membership_config.py` boşken Premium kapalı kalır.

## E. Destek

- E-posta: teknolojimiras@gmail.com  
- Şirket: Miras Teknoloji
