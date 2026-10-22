# Nakitçe

Esnafın cep defteri — satış, veresiye, stok ve günlük nakit akışını tek yerden yöneten Türkçe mobil iş uygulaması.

**Miras Teknoloji** · paket: `com.mirasteknoloji.nakitce` · sürüm: `1.0.0`

## Özellikler

- Gelen / giden para ve kasa bakiyesi
- Veresiye (müşteri bakiyesi, tahsilat, WhatsApp hatırlatma taslağı)
- Stok / hizmet, barkod ile elle arama, hızlı satış
- Pasta grafik ile gelir–gider dağılımı
- POS kesintisi ve teklif (Premium)
- PDF / CSV işletme raporu
- İsteğe bağlı kendi Supabase projenle bulut eşitleme
- GİB e-Arşiv portalına yönlendirme (uygulama içinde fatura kesmez)

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
src/                 Uygulama (main, views, üyelik, sync)
src/assets/          Logo, ikon, Play özellik grafiği
store/               Mağaza metni, veri güvenliği taslağı, checklist
scripts/             AAB derleme ve mağaza görselleri
supabase_schema.sql  Kullanıcının kendi Supabase sync tablosu
membership_schema.sql + supabase/functions/membership/
                     Miras Teknoloji üyelik sunucusu (taslak)
```

## Üyelik (Premium)

İki ayrı Supabase kullanımı vardır:

1. **Kullanıcının projesi** — işletme kayıtlarının eşitlemesi (`supabase_schema.sql`). Ücreti kullanıcı öder.
2. **Miras üyelik projesi** — hesap, deneme ve abonelik yetkisi. Yazma yalnızca Edge Function ile; uygulama `service_role` taşımaz.

Premium erişimi sunucu doğrulamasına bağlıdır. `src/membership_config.py` içine geliştirici proje URL ve public anon key yazılmadan Premium kapalı kalır. Play Billing köprüsü (`src/billing_bridge.py`) henüz stub’tır.

## Android paketleme

Play Store için AAB önerilir; yan yükleme için APK:

```powershell
# Boşluklu Windows kullanıcı adında junction gerekebilir (bkz. store/console_checklist.md)
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
