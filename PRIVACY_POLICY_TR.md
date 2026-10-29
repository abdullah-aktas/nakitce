# Nakitçe Gizlilik Politikası Taslağı

**Son güncelleme:** 21 Ekim 2026

Nakitçe; işletme hareketleri, müşteri veresiye kayıtları, stok, POS ödemeleri ve teklifleri yönetmek için kullanılan bir iş defteridir. Bu metin, uygulamanın mevcut özelliklerine göre hazırlanmış yayın öncesi taslaktır. Google Play'e gönderilmeden önce gerçek işletme iletişim bilgileriyle gözden geçirilmeli ve herkese açık, kalıcı bir HTTPS adresinde yayımlanmalıdır.

## Uygulama içinde tutulan bilgiler

Uygulamaya girdiğiniz gelir-gider hareketleri, müşteri adları ve telefonları, veresiye bakiyeleri, ürün ve barkod bilgileri, POS kayıtları ve teklifler varsayılan olarak cihazınızdaki uygulama depolamasında tutulur. Kamera ile çekilen veya dosyadan seçilen ekler de küçük boyut sınırı içinde cihazda saklanır; bu ekler Supabase eşitlemesine dahil edilmez. Nakitçe bu işletme kayıtlarını kendi sunucularına kendiliğinden göndermez. Bu depolama alanı işletim sistemi tarafından yönetilir; uygulama verileri için uçtan uca şifreleme garantisi verilmez.

## Nakitçe hesabı ve üyelik

Premium deneme veya abonelik için Nakitçe hesabı oluşturursanız e-posta ve parola Miras Teknoloji’nin yönettiği üyelik Supabase projesine gönderilir. Deneme başlangıç/bitiş zamanları sunucu saatiyle kaydedilir. Uygulama, üyelik durumunun son doğrulanmış kopyasını sınırlı süre cihaz önbelleğinde tutabilir; bu önbellek Premium hakkını kendi başına oluşturmaz. Google Play satın alma belirteçleri sunucuda doğrulanır.

## Nakitçe bulutu (isteğe bağlı Premium eşitleme)

Bulut eşitlemesi Miras Teknoloji’nin Nakitçe Supabase projesinde tutulur. Son kullanıcı kendi veritabanı projesi açmaz veya proje anahtarı girmez. Nakitçe hesabınıza giriş yaptıktan sonra (Premium ile) kayıtlarınız yalnızca sizin kullanıcı kimliğinize bağlı tablolara yazılır (RLS). Oturum belirteçleri uygulama çalışırken bellekte ve cihaz tercihlerinde tutulabilir.

## Ses, kamera ve dosya girişi

Konuşarak yaz alanı, varsa cihaz klavyesinin kendi dikte özelliğini kullanır; Nakitçe ses kaydı almaz veya ses dosyası göndermez. Kamera; fiş fotoğrafı veya barkod tarama için kullanıcı açtığında kullanılır. Barkod çözümü cihaz üzerinde (pyzbar) yapılır; görüntü sunucuya gönderilmez. Seçilen fotoğraf ve dosyalar uygulama depolamasında yerel ek olarak tutulur; eşitlemeye dahil edilmez. Metin içeren PDF'lerden metin çıkarımı cihazda yapılır. Fotoğraf OCR için görüntü, tutar/metin çıkarımı amacıyla üçüncü taraf OCR.space hizmetine gönderilebilir (internet gerekir); sonuçlar cihazda işlenir. İlgili düğme resmi GİB portalını açar; Nakitçe GİB parolası veya SMS kodu almaz.
- **WhatsApp / paylaşım:** Hesap ekstresi PDF'i ve nazik hatırlatma metni cihaz paylaşım sayfası veya WhatsApp bağlantısıyla gönderilir.
- **Dosya dışa aktarma:** PDF/CSV dosyaları cihazın dosya kaydetme veya paylaşım arayüzüyle dışa aktarılır.
- **Banka CSV:** Seçtiğiniz dosya cihazda okunur; banka hesabına uzaktan bağlanılmaz.

Nakitçe'nin mevcut sürümünde reklam veya uygulama içi analiz SDK'sı bulunmamaktadır.

## Saklama ve silme

Cihazdaki kayıtları kaldırmak için uygulama verilerini cihaz ayarlarından temizleyebilir veya uygulamayı kaldırabilirsiniz. Üyelik hesabınızı ve bulut eşitleme kopyalarını ilgili Supabase proje panellerinden ayrıca yönetmeniz gerekir.

## Çocukların gizliliği

Nakitçe işletmeler için tasarlanmıştır ve çocuklara yönelik değildir.

## Değişiklikler ve iletişim

Bu politika güncellendiğinde güncel metin yayımlanır. Gizlilik soruları için: **teknolojimiras@gmail.com**.

---

**Yayımdan önce tamamlanacak:** Uygulamanın gerçek veri akışı, dağıtım ülkeleri ve destek kanalıyla metni doğrulayın; taslağı herkese açık HTTPS URL'de yayımlayın ve Play Console'daki Veri güvenliği formunu uygulamanın son sürümüyle tutarlı doldurun.
