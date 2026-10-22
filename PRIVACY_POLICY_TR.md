# Nakitçe Gizlilik Politikası Taslağı

**Son güncelleme:** 21 Ekim 2026

Nakitçe; işletme hareketleri, müşteri veresiye kayıtları, stok, POS ödemeleri ve teklifleri yönetmek için kullanılan bir iş defteridir. Bu metin, uygulamanın mevcut özelliklerine göre hazırlanmış yayın öncesi taslaktır. Google Play'e gönderilmeden önce gerçek işletme iletişim bilgileriyle gözden geçirilmeli ve herkese açık, kalıcı bir HTTPS adresinde yayımlanmalıdır.

## Uygulama içinde tutulan bilgiler

Uygulamaya girdiğiniz gelir-gider hareketleri, müşteri adları ve telefonları, veresiye bakiyeleri, ürün ve barkod bilgileri, POS kayıtları ve teklifler varsayılan olarak cihazınızdaki uygulama depolamasında tutulur. Kamera ile çekilen veya dosyadan seçilen ekler de küçük boyut sınırı içinde cihazda saklanır; bu ekler Supabase eşitlemesine dahil edilmez. Nakitçe bu işletme kayıtlarını kendi sunucularına kendiliğinden göndermez. Bu depolama alanı işletim sistemi tarafından yönetilir; uygulama verileri için uçtan uca şifreleme garantisi verilmez.

## Nakitçe hesabı ve üyelik

Premium deneme veya abonelik için Nakitçe hesabı oluşturursanız e-posta ve parola Miras Teknoloji’nin yönettiği üyelik Supabase projesine gönderilir. Deneme başlangıç/bitiş zamanları sunucu saatiyle kaydedilir. Uygulama, üyelik durumunun son doğrulanmış kopyasını sınırlı süre cihaz önbelleğinde tutabilir; bu önbellek Premium hakkını kendi başına oluşturmaz. Google Play satın alma belirteçleri sunucuda doğrulanır.

## İsteğe bağlı Supabase eşitlemesi

Bulut eşitlemesini siz yapılandırıp hesabınıza bağlarsanız, kayıt defteriniz yapılandırdığınız (sizin) Supabase projesindeki Nakitçe tablosuna gönderilir. Bu proje üyelik sunucusundan ayrıdır; Supabase plan/kullanım ücretini siz ödersiniz. Eşitleme sırasında yazdığınız parola Nakitçe tarafından kaydedilmez. Oturum belirteçleri uygulama çalışırken bellekte tutulur. Proje adresi, public anon/publishable key ve hesap e-postası cihaz tercihlerinde saklanabilir.

## Ses, kamera ve dosya girişi

Konuşarak yaz alanı, varsa cihaz klavyesinin kendi dikte özelliğini kullanır; Nakitçe bu sürümde ses kaydı almaz veya ses dosyası göndermez. Kamera yalnızca kullanıcı fotoğraf çekmeyi seçtiğinde açılır. Seçilen fotoğraf ve dosyalar uygulama depolamasında yerel ek olarak tutulur; eşitlemeye dahil edilmez. Metin içeren PDF'lerden metin çıkarımı cihazda yapılır. Fotoğraf OCR'ı yapılmaz. İlgili düğme resmi GİB portalını açar; Nakitçe GİB parolası veya SMS kodu almaz.
- **WhatsApp:** Borç hatırlatma düğmesi, telefon numarası ve mesaj taslağıyla WhatsApp bağlantısı açar.
- **Dosya dışa aktarma:** PDF/CSV dosyaları cihazın dosya kaydetme arayüzüyle dışa aktarılır.

Nakitçe'nin mevcut sürümünde reklam veya uygulama içi analiz SDK'sı bulunmamaktadır.

## Saklama ve silme

Cihazdaki kayıtları kaldırmak için uygulama verilerini cihaz ayarlarından temizleyebilir veya uygulamayı kaldırabilirsiniz. Üyelik hesabınızı ve bulut eşitleme kopyalarını ilgili Supabase proje panellerinden ayrıca yönetmeniz gerekir.

## Çocukların gizliliği

Nakitçe işletmeler için tasarlanmıştır ve çocuklara yönelik değildir.

## Değişiklikler ve iletişim

Bu politika güncellendiğinde güncel metin yayımlanır. Gizlilik soruları için: **teknolojimiras@gmail.com**.

---

**Yayımdan önce tamamlanacak:** Uygulamanın gerçek veri akışı, dağıtım ülkeleri ve destek kanalıyla metni doğrulayın; taslağı herkese açık HTTPS URL'de yayımlayın ve Play Console'daki Veri güvenliği formunu uygulamanın son sürümüyle tutarlı doldurun.
