# Nakitçe Supabase (Miras projesi)

Tek proje: **üyelik + bulut defter**. Son kullanıcı kendi Supabase açmaz.

## Tablolar

| Tablo / görünüm | Kim kullanır | Amaç |
|-----------------|--------------|------|
| `memberships` | Edge Function (+ kullanıcı SELECT) | Premium / deneme |
| `nakitce_snapshots` | Uygulama REST | Cihaz ↔ bulut JSON defter |
| `nakitce_overview` | Yönetim (SQL) | Hızlı özet görünüm |

Eski ayrı `customers` / `transactions` tabloları ve expand tetikleyicisi **kaldırıldı** — uygulama zaten yalnızca snapshot kullanıyor.

## Kurulum (Dashboard)

1. Supabase’de proje oluştur  
2. **SQL Editor** → `migrations/20261024000000_init.sql` dosyasının tamamını çalıştır  
3. **Edge Functions** → `membership` fonksiyonunu deploy et  
4. `src/membership_config.py` içine Project URL + anon key yaz  

### CLI ile

```bash
supabase login
supabase link --project-ref <PROJECT_REF>
supabase db push
supabase functions deploy membership
```

## Uygulama akışı

1. Kullanıcı Nakitçe hesabı açar / girer (Auth)  
2. `membership` → `status` ile Premium doğrulanır  
3. Premium + oturum varken `nakitce_snapshots` eşitlenir  

`service_role` asla uygulamaya konmaz.

## Abonelik ve gelir (güncel)

Gelir yolları:
1. **Aktivasyon kodu** (çalışır): kodları Supabase SQL Editor'de üret, bayi/web/WhatsApp ile sat.
   `select * from public.generate_activation_codes(50, 365, 'ocak-2027');`  → 50 adet 365 günlük kod.
   Kullanıcı uygulamada Üyelik → Aktivasyon kodu alanına girer; süre mevcut Premium'a eklenir.
2. **Google Play aboneliği**: sunucu doğrulaması hazır (`verify_play_purchase`). Gerekenler: Play Console'da
   `nakitce_premium_monthly` / `nakitce_premium_yearly` ürünleri, `supabase secrets set GOOGLE_SERVICE_ACCOUNT_JSON=...`
   ve uygulamada Play Billing köprüsü (`src/billing_bridge.py` şu an kapalı).
3. **Web ödeme bağlantısı**: `src/membership_config.py` içinde `PAYMENT_URL` doldurulursa Üyelik ekranında düğme çıkar.

Gelir özeti: `select * from public.nakitce_revenue_overview;`
Yayından önce Auth → SMTP ayarına özel e-posta sağlayıcısı bağla (varsayılan SMTP çok düşük limitlidir).
`PRIVACY_URL` ve `SUPPORT_EMAIL` değerlerini `membership_config.py` içinde doldur.
