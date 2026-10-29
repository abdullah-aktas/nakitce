# Nakitçe

Esnafın cebindeki kasa defteri — **Aldım / Verdim**, veresiye, stok ve nakit akışı. Muhasebe jargonu yok.

**Miras Teknoloji** · paket: `com.mirasteknoloji.nakitce` · sürüm: `1.0.0`

## Özellikler

- **Aldım / Verdim** sadelik + sesle komut (“Ahmet'e 450 TL veresiye yaz”)
- Veresiye defteri, vade ve **WhatsApp + profesyonel PDF hesap ekstresi** (mesaj + tablo)
- Kamerayla / PDF ile fiş okuma (OCR; internetli fotoğraf, metinli PDF yerelde)
- Kritik gün hatırlatıcıları (KDV, BA-BS, müşteri vadesi — bilgilendirme amaçlı)
- Pasta grafik, stok, hızlı satış
- **Serbest bölge (ücretsiz):** kasa, veresiye, WhatsApp ekstre, OCR, stok
- **Premium:** POS tahsilat takibi, teklif, banka CSV, bulut, 12 aylık grafik
- Nakitçe bulutu (Miras Supabase) — kullanıcı kendi proje açmaz; hesapla giriş + Premium eşitleme
- GİB e-Arşiv: hazırlık panoya + resmi portal (uygulama içinde fatura kesmez)
- SoftPOS / temassız kart okuma **yok** (lisanslı banka ürünü gerekir); kart satışlarının hesaba geçişini takip edersin

## Supabase (yalnızca geliştirici — Miras projesi)

Ayrıntı: [`supabase/README.md`](supabase/README.md)

1. Supabase’de proje aç  
2. SQL: `supabase/migrations/20261024000000_init.sql`  
   (eski expand tabloları varsa `…000001_drop_legacy_expand.sql`)  
3. `supabase functions deploy membership`  
4. `src/membership_config.py` → URL + anon key  

Kullanıcı yalnızca Nakitçe hesabıyla girer. Veri: `memberships` + `nakitce_snapshots` (RLS).

## Gereksinimler

- Python ≥ 3.12
- [Flet](https://flet.dev/) (geliştirme için `flet-cli`, `flet-desktop`)

```bash
cd nakitce
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -e .
pip install flet-cli flet-desktop
```

## Çalıştırma

```bash
flet run src/main.py
```

veya proje kökünden:

```bash
flet run
```

(`pyproject.toml` içinde `[tool.flet.app] path = "src"` tanımlıdır.)

## Proje yapısı

```
src/                 Uygulama (main, views, üyelik, sync, OCR, ses komutu)
src/assets/          Logo, ikon, Play özellik grafiği
store/               Mağaza metni, veri güvenliği taslağı, checklist
scripts/             AAB derleme ve mağaza görselleri
supabase/            Tek Miras proje: migrations + membership Edge Function
```

## Üyelik (Premium)

Tek Miras Supabase projesi: üyelik + işletme verisi. Kullanıcı kendi proje açmaz.

Premium erişimi sunucu doğrulamasına bağlıdır. `src/membership_config.py` doldurulmadan Premium ve bulut kapalı kalır. Play Billing köprüsü (`src/billing_bridge.py`) henüz stub’tır — çalışmayan satın alma düğmesi gösterilmez.

## Android paketleme

### Uygulama ikonu

Mavi–teal geçiş üzerinde kırmızı kalp ve altın ₺ ikonunu yeniden üretmek için:

```powershell
python scripts\generate_icon.py
```

Pillow proje bağımlılıklarına dahildir. Betik, depodaki DejaVu Sans fontunu
kullanır; sistem fontu veya ek indirme gerektirmez. Çıktılar:

- `src/assets/icon.png`: 1024×1024, yuvarlatılmış şeffaf köşeler; uygulama ve Flet paketleme.
- `store/assets/icon_512.png`: 512×512, opak kare; köşe ve gölge işlemini Google Play uygular.

Yollar çalışma dizinine değil, proje köküne göre belirlenir.
`python scripts\export_store_assets.py` de aynı ikon üreticisini kullanır.
SVG ikon ve logo da aynı mavi–teal, kırmızı kalp ve altın ₺ tasarımını kullanır.
`python scripts\export_store_assets.py`, özellik grafiğinin iki PNG kopyasını da
günceller; büyük marka işareti ve telefon içindeki küçük ikon yeni uygulama
ikonundan üretilir. SVG sürümleri vektöreldir; ₺ işareti font gerektirmez.

### Derleme

Play Store için AAB önerilir; yan yükleme için APK:

```powershell
.\scripts\build_play_aab.ps1          # AAB → build\aab\
flet build apk --module-name main     # APK → build\apk\
```

Play’e yüklemek için upload keystore ile imzalayın. Ayrıntılar: [PLAY_STORE_RELEASE.md](PLAY_STORE_RELEASE.md) ve [store/console_checklist.md](store/console_checklist.md).

Mağaza metni ve grafikler: `store/listing_tr.txt`, `store/assets/`.

## Gizlilik

Taslak: [PRIVACY_POLICY_TR.md](PRIVACY_POLICY_TR.md) — Play Console’a girmeden önce HTTPS üzerinde yayımlanmalıdır.

## Lisans / iletişim

Copyright © 2026 Miras Teknoloji  
Destek: teknolojimiras@gmail.com  
Depo: https://github.com/abdullah-aktas/nakitce
