# Play Console — Veri güvenliği formu (Nakitçe taslak yanıtları)

Uygulamanın **fiili davranışına** göre doldurun. Üyelik Supabase veya kullanıcı sync bağlandıktan sonra formu gözden geçirin.

## Veri toplama / paylaşma özeti

| Veri türü | Toplanıyor mu? | Paylaşılıyor mu? | Amaç | Zorunlu mu? |
|-----------|----------------|------------------|------|-------------|
| Uygulama etkinliği (işlem kayıtları) | Evet (cihazda) | Hayır (varsayılan) | Uygulama işlevselliği | Hayır — kullanıcı girer |
| Kişisel bilgiler (e-posta, işletme profili) | İsteğe bağlı üyelik/profil | Üyelik için Miras Supabase’e | Hesap / üyelik | Hayır |
| Finansal bilgiler (tutarlar, bakiyeler) | Evet (cihazda) | Nakitçe hesabı + Premium bulut eşitlemesinde Miras Nakitçe sunucusuna (kullanıcıya özel RLS) | Uygulama işlevselliği | Hayır |
| Fotoğraflar / belgeler | İsteğe bağlı ekler | OCR kullanıldığında görsel OCR.space’e gider; aksi halde cihazda kalır (bulut sync’e dahil değil) | Uygulama işlevselliği | Hayır |
| Cihaz kimlikleri | Hayır (bilinen SDK yok) | Hayır | — | — |
| Konum | Hayır | Hayır | — | — |

## Öne çıkan yanıtlar

- **Uygulama kullanıcı verilerini topluyor mu?** Evet (cihaz depolama + isteğe bağlı hesap/üyelik + isteğe bağlı kullanıcı Supabase sync).
- **Veriler şifrelenerek aktarılıyor mu?** HTTPS üzerinden (Supabase Auth/REST). Cihaz içi uçtan uca şifreleme iddiası yok.
- **Kullanıcı veri silebilir mi?** Cihaz verisi uygulama verilerini silerek; üyelik/sync kopyaları ilgili Supabase panellerinden.
- **Veri satışı / reklam / analitik SDK?** Hayır (mevcut sürüm).
- **Çocuklara yönelik mi?** Hayır.

## İzinler (manifest)

- `INTERNET` — üyelik, sync, dış bağlantılar (GİB, WhatsApp)
- `CAMERA` — isteğe bağlı fiş/fotoğraf ekleme (`flet-camera`)
- Depolama / `READ_MEDIA_*` — **istemeyin**; FilePicker SAF kullanır

## Abonelik / satın alma

Premium için Play Billing bağlandığında Veri güvenliği ve Finans formlarında abonelik satın alma bilgisini güncelleyin. Satın alma belirteci yalnızca geliştirici üyelik sunucusuna doğrulama için gönderilir.
