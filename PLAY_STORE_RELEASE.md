# Nakitçe — Google Play yayın rehberi

Bu dosya Play Store hazırlığını tek yerde toplar. Yapıştırılabilir metinler ve form yanıtları `store/` klasöründedir.

## Hızlı durum

| Kalem | Durum |
|-------|--------|
| Uygulama adı / paket | Nakitçe · `com.mirasteknoloji.nakitce` |
| Sürüm | `1.0.0` (build `1`) |
| İkon / özellik grafiği | `store/assets/` (+ `src/assets/`) |
| Mağaza metni | `store/listing_tr.txt` |
| Veri güvenliği taslağı | `store/data_safety_tr.md` |
| Kontrol listesi | `store/console_checklist.md` |
| AAB betiği | `scripts/build_play_aab.ps1` |
| AAB çıktısı | `build/aab/nakitce.aab` (üretilmiş; Play için **upload keystore ile yeniden imzala**) |
| Gizlilik metni | `docs/privacy.html` → `https://abdullah-aktas.github.io/nakitce/privacy.html` |
| Play Billing / ürün kimlikleri | Henüz bağlı değil — Premium’u üretim özelliği gibi sunma |

## 1. Mağaza varlıkları

```powershell
python scripts\export_store_assets.py
```

- Simge: `store/assets/icon_512.png` (512×512, opak kare; kırmızı kalp + altın ₺)
- Uygulama ikonu: `src/assets/icon.png` (1024×1024); yalnızca ikonları yenilemek için `python scripts\generate_icon.py`
- Özellik grafiği: `store/assets/play_feature_graphic.png` (1024×500)
- Ekran görüntüleri: `store/assets/screenshots/` (1080×1920, 5 adet; `python scripts\generate_play_screenshots.py`)
  - İdeal ek: gerçek Android cihazdan 2+ görüntü

## 2. AAB üretimi

Bu makinede AAB bir kez başarıyla üretildi: **`build/aab/nakitce.aab`**.

Play’e yüklemek için upload keystore ile yeniden derleyin:

```powershell
# İlk kez (boşluklu kullanıcı adı için; yönetici gerekmez):
# mklink /J C:\AndroidSdk "%LOCALAPPDATA%\Android\Sdk"
# mklink /J C:\fh "%USERPROFILE%"

$env:FLET_ANDROID_SIGNING_KEY_STORE="$env:USERPROFILE\nakitce-upload.jks"
$env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD="..."
$env:FLET_ANDROID_SIGNING_KEY_PASSWORD="..."
$env:FLET_ANDROID_SIGNING_KEY_ALIAS="upload"
.\scripts\build_play_aab.ps1
```

Çıktı: `build\aab\nakitce.aab`. Play’e **AAB** yükleyin (APK değil). Debug imzalı paket Play’e kabul edilmez.

## 3. Play Console adımları

1. Uygulama oluştur → ad **Nakitçe**.
2. Dahili test kanalına AAB yükle; paket ID’yi doğrula.
3. `store/listing_tr.txt` içeriğini Mağaza listesine yapıştır.
4. Grafikleri ve en az 2 telefon ekran görüntüsü ekle.
5. Gizlilik politikası HTTPS URL’sini gir.
6. `store/data_safety_tr.md` ile Veri güvenliği formunu doldur.
7. İçerik derecelendirmesi + hedef kitle (çocuklara yönelik değil).
8. Ücretli üyelik açılacaksa Monetization’da ürünleri oluştur:
   - `nakitce_premium_monthly`
   - `nakitce_premium_yearly`
   - İsteğe bağlı 30 gün deneme offer
9. Üyelik Supabase + Edge Function + Billing köprüsü hazır olmadan aboneliği production’da açma.
10. Dahili/kapalı test → üretim.

Güncel Flet paketleme: https://flet.dev/docs/publish/android

## 4. Üyelik mimarisi (hatırlatma)

1. Tek Miras Supabase → Auth + `memberships` + `nakitce_snapshots` (`supabase/migrations` + Edge Function `membership`)
3. Deneme sunucu saatiyle başlar; cihaz sayacı yoktur
4. Play token sunucuda doğrulanır; `service_role` uygulama içinde olmaz
5. SharedPreferences yalnızca sınırlı UI önbelleğidir

## 5. Fiyat önerisi (taslak)

- Temel: ücretsiz (ayda 30 Aldım/Verdim, ayda 8 WhatsApp; veresiye sınırsız)
- Premium: **₺99,99/ay** veya **₺999,99/yıl** (öneri; Play fiyatı bağlayıcıdır)

## 6. Bilinen sınırlar

- Bu ortam Play’e yükleme yapamaz; AAB’yi kendi makinenizde üretin.
- Billing köprüsü stub; Edge Function’da Play API doğrulaması tamamlanmalı.
- `membership_config.py` boşken Premium kapalı kalır.
- GİB yalnızca resmi portal yönlendirmesidir; kamera barkod okuyucu yoktur.
- Pasta grafik SVG ile çizilir (`flet-charts` AAB derlemesinde Flet 0.82 ile uyumsuzdu; kaldırıldı).
- Windows’ta kullanıcı/SDK yolunda **boşluk** varsa Gradle/NDK derlemesi sık düşer. `C:\AndroidSdk` junction + mümkünse Flutter’ı boşluksuz yola alın; alternatif: [Flet Studio](https://flet.dev/docs/publish/android) bulut AAB.
- Proje yolunda Türkçe karakter varsa Gradle ve Dart AOT derleyicisi hata verebilir. Bu durumda kaynakları ASCII karakterli bir derleme dizinine kopyalayıp orada derleyin; yalnızca Gradle yol kontrolünü kapatmak yeterli değildir.
