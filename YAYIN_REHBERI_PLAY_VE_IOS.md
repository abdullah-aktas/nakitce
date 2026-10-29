# Nakitçe — Google Play ve App Store (iOS) yayın rehberi

Uygulama: **Nakitçe** · Paket/Bundle ID: `com.mirasteknoloji.nakitce` · Sürüm `1.0.0` (build `1`) · Geliştirici: Miras Teknoloji · Flet 1.0.5 (Python)

> Önemli: Google Play ve App Store'da dijital abonelik/premium satışı **mağazanın kendi ödeme sistemiyle** yapılmak zorundadır. Uygulamada Play Billing/StoreKit köprüsü henüz yok (`src/billing_bridge.py` kapalı). Ayrıca aktivasyon kodu girişi ve harici "Web'den satın al" düğmesi mağaza kurallarına takılabilir (bkz. Bölüm 5). İlk sürümü **ücretsiz + deneme** olarak yayınlayıp ödeme entegrasyonunu sonraki sürümde eklemek en güvenli yoldur.

---

## 0. Ortak hazırlık (iki mağaza için)

1. **Gizlilik politikası URL'si (HTTPS, herkese açık)**: `PRIVACY_POLICY_TR.md` içeriğini bir web sayfasına koy (GitHub Pages, Google Sites, kendi sitesi). Adresi `src/membership_config.py` içindeki `PRIVACY_URL`'e yaz. Politikayı gerçek davranışa göre güncelle: hesap e-postası, Supabase bulut eşitleme, fiş OCR'ının internetteki servise gönderilmesi, hesap silme.
2. **Destek e-postası/web sitesi**: `SUPPORT_EMAIL` doldur (örn. teknolojimiras@gmail.com).
3. **Hesap silme sayfası**: Google Play, hesap oluşturulan uygulamalarda hem uygulama içinde hem **web üzerinde hesap silme talebi bağlantısı** ister. Uygulama içi silme hazır (Üyelik → Hesabımı sil). Web için basit bir sayfa: "Hesabı silmek için uygulamada Üyelik → Hesabımı sil veya teknolojimiras@gmail.com adresine kayıtlı e-postanla yaz."
4. **Supabase üretim ayarları**: Auth → SMTP'ye özel e-posta sağlayıcısı bağla (varsayılan SMTP çok düşük limitli; doğrulama maili gitmezse kullanıcı giriş yapamaz). Auth → URL Configuration → Site URL'i ayarla. Test hesabıyla kayıt → doğrulama → giriş akışını dene.
5. **Test hesabı**: Mağaza incelemecisi için e-postası doğrulanmış bir demo hesap hazırla (inceleme notlarına yaz).
6. **Mağaza varlıkları**: `python scripts\export_store_assets.py` → `store/assets/icon_512.png`, `play_feature_graphic.png`. Metinler: `store/listing_tr.txt`.
7. **Gerçek ekran görüntüleri**: Uygulamayı gerçek cihazda/emülatörde aç; boş değil, birkaç gerçek-benzeri kayıtla çek (kendi test kayıtlarını girip sonra sil). Gerçek kişi verisi kullanma.
8. **Sürüm**: `pyproject.toml` içinde `version` ve `build_number`. Her yüklemede `build_number` artmalı.
9. **Yasal**: Uygulama resmî defter/e-Fatura/yazar kasa yerine geçmez notu uygulamada var; mağaza açıklamasında da belirt. Miras Teknoloji'nin vergi/şirket bilgileri geliştirici hesabıyla uyumlu olmalı.

---

## 1. GOOGLE PLAY

### 1.1 Geliştirici hesabı
1. https://play.google.com/console → Google hesabıyla giriş.
2. Tek seferlik **25 USD** kayıt ücreti.
3. Hesap türü: **Kişisel** veya **Kuruluş**. Kuruluş için D-U-N-S numarası gerekir (Miras Teknoloji şirketse bu tercih edilir).
4. Kimlik/adres doğrulaması (birkaç gün sürebilir). Para kazanacaksan **ödeme profili** (Merchant) oluştur, vergi bilgilerini doldur.
5. **Kişisel hesaplarda (2023 sonrası açılanlar)**: üretim sürümüne çıkmadan önce **en az 12 test kullanıcısıyla 14 gün kapalı test** zorunludur. Kuruluş hesaplarında bu şart yoktur. Güncel koşulu Console'da doğrula.

### 1.2 Android derleme ortamı (Windows)
- Flutter + Android SDK + JDK kurulu olmalı (Flet bunu ilk derlemede ister/indirir).
- Kullanıcı adında boşluk var → `PLAY_STORE_RELEASE.md` içindeki `mklink /J` çözümünü uygula (`C:\AndroidSdk`, `C:\fh`).

### 1.3 Upload keystore (bir kez, SAKLA)
```powershell
keytool -genkeypair -v -keystore $env:USERPROFILE\nakitce-upload.jks -alias upload -keyalg RSA -keysize 2048 -validity 10000
```
- `.jks` dosyasını ve parolaları **güvenli yerde yedekle**; repoya koyma (`secrets/` gitignore'da olmalı).
- Play App Signing açık olacağı için upload anahtarı kaybolursa Google üzerinden sıfırlanabilir; yine de yedekle.

### 1.4 AAB üretimi
```powershell
$env:FLET_ANDROID_SIGNING_KEY_STORE="$env:USERPROFILE\nakitce-upload.jks"
$env:FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD="..."
$env:FLET_ANDROID_SIGNING_KEY_PASSWORD="..."
$env:FLET_ANDROID_SIGNING_KEY_ALIAS="upload"
.\scripts\build_play_aab.ps1
```
Çıktı: `build\aab\nakitce.aab`. Play'e **AAB** yüklenir (APK değil). Hedef API düzeyi Google'ın güncel şartını sağlamalı (Flet'in kullandığı Flutter sürümü genelde karşılar; Console yükleme sırasında uyarır).

Yüklemeden önce bir **APK** ile gerçek cihazda dene: `flet build apk`, `adb install`. Kontrol: boş açılış, kayıt ekleme/silme, kamera izni, PDF/WhatsApp paylaşımı, hesap oluşturma, kod kullanma.

### 1.5 Play Console'da uygulama oluşturma
1. **Uygulama oluştur** → ad: Nakitçe, dil: Türkçe, Uygulama (oyun değil), **Ücretsiz**. (Ücretsiz/ücretli seçimi sonradan değişmez; abonelik uygulama içi üründür, ücretsiz seç.)
2. **Panel → Uygulamanızı ayarlayın** listesini tamamla:

| Bölüm | Ne girilir |
|---|---|
| Gizlilik politikası | HTTPS URL |
| Uygulama erişimi | Giriş gerektiren bölümler için test hesabı (e-posta + parola) ve talimat |
| Reklamlar | Reklam yok |
| İçerik derecelendirme | Anket (finans/iş aracı; şiddet vb. yok) → genelde 3+ |
| Hedef kitle | 18+ / yetişkin; çocuklara yönelik değil |
| Veri güvenliği | `store/data_safety_tr.md` esas: e-posta, kullanıcı kimliği, finansal bilgi (kullanıcının girdiği kayıtlar, bulut eşitlemesinde), fotoğraf (OCR); aktarımda şifreleme evet; silme talebi yolu evet |
| Hükümet/finans uygulaması | Kredi/ödünç vermez; "kasa defteri" olarak beyan et |
| Haber/COVID/sağlık | Hayır |
| **Finansal özellikler beyanı** | Banka, kredi, ödeme işlemi yapmadığını belirt; veresiye *takip defteridir* |
| Reklam kimliği | Kullanmıyor |
| Kategori / iletişim | Kategori: İş / Finans; e-posta, (opsiyonel) web sitesi |

3. **Mağaza girişi** (Ana mağaza girişi): `store/listing_tr.txt` içeriği; 512×512 simge, 1024×500 özellik grafiği, en az 2 (ideal 4-8) telefon ekran görüntüsü. Açıklamada "resmî muhasebe/e-Fatura yerine geçmez" ifadesi olsun. Aldatıcı iddia (örn. "GİB onaylı") kullanma.
4. **İzin beyanları**: Kamera (fiş/barkod), internet. Depolama izinleri istenmiyor (SAF).

### 1.6 Abonelik ürünleri (ödeme açılacaksa)
1. Play Console → Para kazanma → **Abonelikler** → ürün oluştur: `nakitce_premium_monthly`, `nakitce_premium_yearly` (kodda bu kimlikler bekleniyor). Fiyat: ör. 99,99 TL/ay, 999,99 TL/yıl; ücretsiz deneme/teklif tanımlayabilirsin.
2. Google Cloud'da **servis hesabı** oluştur, Play Console → Kullanıcılar ve izinler → servis hesabını ekle (Finansal verileri görüntüleme + Siparişleri yönetme). JSON anahtarı:
```powershell
npx supabase secrets set GOOGLE_SERVICE_ACCOUNT_JSON='{...}' --project-ref cdxyxohetqwfwnozhjxw
npx supabase secrets set GOOGLE_PLAY_PACKAGE_NAME=com.mirasteknoloji.nakitce --project-ref cdxyxohetqwfwnozhjxw
```
(Edge function'ın okuduğu gerçek secret adlarını `supabase/functions/membership/index.ts` başında doğrula.)
3. İstemci tarafında Play Billing köprüsü (`billing_bridge.py`) yazılıp satın alma `obfuscatedExternalAccountId = Supabase user.id` ile başlatılmalı. Bu yapılmadan "Google Play'den satın al" düğmesi görünmez (şu anki doğru davranış).
4. Gerçek satın alma testi: Ayarlar → Lisans testi'ne test hesaplarını ekle, **iç test** kanalından yükle.

### 1.7 Yayın akışı
1. **Test → Dahili test**: AAB yükle → sürüm notu → test kullanıcı e-posta listesi → kaydet/yayınla. Opt-in linkiyle gerçek cihazda dene.
2. (Kişisel hesapsa) **Kapalı test**: 12+ test kullanıcı, 14 gün sürekli katılım. Geri bildirim topla.
3. **Üretim → Yeni sürüm**: AAB seç → sürüm adı `1.0.0` → notlar → **İncelemeye gönder**. İnceleme birkaç saatten birkaç güne kadar sürer.
4. **Aşamalı yayın** (örn. %20) seçip sorun yoksa %100'e çıkar.
5. Güncelleme: `build_number`'ı artır → yeni AAB → aynı akış.

### 1.8 Sık ret nedenleri
- Gizlilik URL'si yok/çalışmıyor; Veri güvenliği formu gerçeğe uymuyor.
- Test hesabı verilmemiş veya çalışmıyor (doğrulama maili gelmiyor → SMTP!).
- Hesap silme yolu eksik.
- Mağaza ödeme sistemi dışında dijital abonelik satışı (Bölüm 5).
- Debug imzalı/yanlış anahtarla imzalı paket.

---

## 2. APPLE APP STORE (iOS)

### 2.1 Gereksinimler
- **Mac + Xcode** zorunlu (Flet iOS derlemesi macOS'ta yapılır; Windows'ta derlenemez). Mac yoksa: bir Mac kirala/bulut Mac (MacinCloud vb.) veya GitHub Actions `macos` runner'ı.
- **Apple Developer Program**: 99 USD/yıl. https://developer.apple.com/programs/ — Kişisel veya Kuruluş (D-U-N-S gerekir). Onay 1-3 gün (kuruluşta daha uzun).
- Mac'te: Flutter, Xcode + komut satırı araçları, CocoaPods (`sudo gem install cocoapods`), Python 3.12, `pip install flet-cli==1.0.5`.

### 2.2 Apple tarafında tanımlar
1. developer.apple.com → Certificates, IDs & Profiles → **Identifiers** → App ID: Bundle ID `com.mirasteknoloji.nakitce` (explicit). Gerekli yetenekler: yok (Sign in with Apple gerekmiyor çünkü üçüncü taraf sosyal giriş yok; e-posta/parola kendi hesabın).
2. **Certificates**: *Apple Distribution* sertifikası (Xcode → Settings → Accounts → Manage Certificates ile otomatik de olur).
3. **Provisioning Profile**: App Store türünde, bu Bundle ID + Distribution sertifikası. (Xcode "Automatically manage signing" ile otomatik oluşturabilir.)
4. https://appstoreconnect.apple.com → **Apps → + → New App**: Platform iOS, ad Nakitçe (benzersiz olmalı; doluysa "Nakitçe - Kasa Defteri" gibi), birincil dil Türkçe, Bundle ID seç, SKU (örn. `nakitce-ios-1`).

### 2.3 pyproject.toml'a iOS ayarları
```toml
[tool.flet.ios]
bundle_id = "com.mirasteknoloji.nakitce"
team_id = "XXXXXXXXXX"            # Apple Developer Team ID
export_method = "app-store"

[tool.flet.ios.info]
NSCameraUsageDescription = "Fiş ve barkod okumak için kamera kullanılır."
NSPhotoLibraryUsageDescription = "Fiş görseli seçmek için fotoğraf kitaplığına erişilir."
ITSAppUsesNonExemptEncryption = false
```
- `ITSAppUsesNonExemptEncryption=false`: yalnızca standart HTTPS kullanılıyorsa; ihracat uyumluluk sorusunu atlatır.
- İzin metinleri Türkçe ve **gerçek kullanım amacını** anlatmalı; yoksa ret/çökme olur.
- `build_number`'ı her yüklemede artır.

### 2.4 Derleme ve yükleme (Mac'te)
```bash
flet build ipa --verbose
```
Çıktı `build/ipa/*.ipa`. Yükleme seçenekleri:
- **Transporter** uygulaması (Mac App Store'dan) → IPA'yı sürükle → Deliver, veya
- `xcrun altool --upload-app -f build/ipa/Nakitce.ipa -t ios -u APPLE_ID -p APP_SPECIFIC_PASSWORD`, veya
- Xcode → Organizer → Distribute App → App Store Connect.

İşlem sonrası App Store Connect'te build "İşleniyor" görünür (10-30 dk), sonra TestFlight'ta çıkar.

### 2.5 TestFlight
1. App Store Connect → TestFlight → build'e "Export Compliance" sorusunu yanıtla (standart şifreleme/HTTPS).
2. **İç test** (ekibin, 100 kişiye kadar, inceleme yok) ve **dış test** (10.000 kişiye kadar, kısa Beta incelemesi).
3. Gerçek iPhone'da dene: kamera izni, PDF kaydet/paylaş, WhatsApp paylaşımı, hesap oluşturma, kod kullanma.

### 2.6 Mağaza sayfası (App Store Connect → sürüm 1.0)
| Alan | İçerik |
|---|---|
| Ad (30 karakter), Alt başlık (30) | `store/listing_tr.txt`'ten kısalt |
| Açıklama, Anahtar kelimeler (100), Promosyon metni | Türkçe; "resmî muhasebe yerine geçmez" |
| Destek URL'si | Zorunlu (web sayfası) |
| Gizlilik politikası URL'si | Zorunlu |
| Kategori | İş (Business) veya Finans |
| Yaş derecelendirmesi | Anket; genelde 4+ |
| Ekran görüntüleri | **6,7" (1290×2796 veya 1320×2868)** zorunlu; 6,5"/iPad (iPad desteği açıksa) gerekebilir. Gerçek cihaz/simülatörden |
| Simge | 1024×1024, **alfa/saydamlık yok**, köşeleri yuvarlatma |
| Telif hakkı | `2026 Miras Teknoloji` |
| İnceleme bilgileri | Demo hesap (e-posta + parola), iletişim telefonu/e-posta, notlar |

**App Privacy (Gizlilik "beslenme etiketleri")**: Toplanan veri: E-posta adresi, Kullanıcı kimliği, Finansal bilgi/Diğer kullanıcı içeriği (bulut eşitleme), Fotoğraflar (OCR). Hepsi "Uygulama işlevselliği"; takip (tracking) **yok**. Veri kullanıcıya bağlı.

### 2.7 Apple'a özel kurallar (ret riskleri)
- **Hesap silme (Guideline 5.1.1(v))**: hesap oluşturan uygulamalar uygulama içinde silme sunmalı → hazır (Üyelik → Hesabımı sil). İnceleme notunda yolu belirt.
- **Dijital içerik satışı (3.1.1)**: Premium için **uygulama içi satın alma (StoreKit/App Store abonelikleri)** zorunlu. Aktivasyon kodu girişi: kodlar uygulama dışında satılıp uygulamada açılıyorsa Apple bunu genelde kabul etmez (özellikle iOS'ta). Harici "Web'den satın al" bağlantısı da yalnızca belirli bölge/koşullarda serbesttir. **iOS sürümünde bu iki düğmeyi gizle** ve Premium'u StoreKit ile sun ya da ilk iOS sürümünü tamamen ücretsiz yayınla.
- **Minimum işlevsellik (4.2)**: Basit web sarmalayıcı sanılmamalı; mevcut yerel özellikler yeterli.
- **Çalışmayan özellik**: Placeholder/ölü düğme bırakma; Play Billing düğmesi zaten gizli.
- **Finans uygulaması**: Kredi/yatırım aracı değil, yalnızca defter olduğunu açıkla.
- Demo hesap çalışmalı (SMTP sorunu yine kritik).

### 2.8 İncelemeye gönderme
1. Build'i sürüme ata → tüm alanlar tamam → **Add for Review → Submit**.
2. İnceleme genelde 24-48 saat. Ret gelirse Resolution Center'dan yanıtla, düzelt, yeni build yükle.
3. Yayın seçeneği: otomatik, manuel veya tarih; **aşamalı sürüm (7 gün)** seçilebilir.

### 2.9 iOS için StoreKit (ödeme açılacaksa)
- App Store Connect → Abonelikler → abonelik grubu + `nakitce_premium_monthly/yearly` ürünleri, fiyatlar, yerelleştirme, inceleme ekran görüntüsü.
- **Paid Applications Agreement**, banka ve vergi bilgileri (Agreements, Tax, and Banking) tamamlanmadan satın alma çalışmaz.
- Sunucu doğrulaması için App Store Server API / Server Notifications v2 gerekir; edge function'a ayrı bir `verify_apple_purchase` eklenmeli (şu an yok). Apple komisyonu: Small Business Program ile %15.

---

## 3. Gelir modeli önerisi (mağaza kurallarına uygun)
| Kanal | Çözüm | Durum |
|---|---|---|
| Android | Play Billing abonelik + sunucu doğrulama | Sunucu hazır, istemci köprüsü yazılacak |
| iOS | StoreKit abonelik + App Store Server API | Yapılacak |
| Web / kurumsal / bayi | Aktivasyon kodu (**yalnızca Android/web sürümünde**), banka havalesi | Çalışıyor; iOS'ta gizle |
| Deneme | 30 gün (e-posta doğrulamasıyla) | Çalışıyor |

Pratik yol: **1) Android'de ücretsiz + deneme + kod ile yayınla, 2) Play Billing köprüsünü ekle, 3) iOS'u StoreKit'le birlikte çıkar.**

---

## 4. Yayın öncesi son kontrol listesi
- [ ] `PRIVACY_URL`, `SUPPORT_EMAIL` dolu; gizlilik politikası yayında ve gerçeğe uygun
- [ ] Supabase özel SMTP; kayıt→doğrulama→giriş test edildi
- [ ] Demo hesap hazır (e-posta doğrulanmış, bazı gerçek-benzeri kayıtlar)
- [ ] Gerçek cihazda: boş açılış, kayıt ekle/sil, kasa/bakiye doğru, PDF, WhatsApp, kamera izni, çevrimdışı açılış
- [ ] Hesap silme uygulama içinde ve web'de erişilebilir
- [ ] Veri güvenliği (Play) / App Privacy (Apple) formları aynı gerçeği anlatıyor
- [ ] Ekran görüntüleri, simge (iOS'ta alfasız), açıklama metinleri hazır
- [ ] Keystore ve Apple sertifikaları yedekli, repoda yok
- [ ] `build_number` artırıldı; `git tag v1.0.0`
- [ ] iOS'ta kod girişi/harici ödeme düğmeleri gizli; ödeme yalnızca mağaza sistemiyle

## 5. Süre tahmini
| Adım | Süre |
|---|---|
| Play hesabı doğrulama | 1-5 gün |
| Play kapalı test (kişisel hesap) | 14 gün |
| Play inceleme | 1-7 gün |
| Apple Developer onayı | 1-7 gün |
| Apple inceleme | 1-3 gün |

Resmî kaynaklar: Play Console Yardım (support.google.com/googleplay/android-developer), App Store Review Guidelines (developer.apple.com/app-store/review/guidelines), Flet yayın dokümanları (flet.dev/docs/publish).
