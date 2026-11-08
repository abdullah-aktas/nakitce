"""Miras Teknoloji · Nakitçe Supabase (tek proje).

Son kullanıcı kendi Supabase açmaz. Yalnızca Nakitçe hesabıyla giriş yapar.

Kurulum: supabase/README.md
  1) migrations/20261024000000_init.sql  (+ isteğe bağlı drop_legacy)
  2) functions/membership deploy
  3) Aşağıya Project URL + publishable/anon key

Asla service_role koyma.
"""

MEMBERSHIP_SUPABASE_URL = "https://cdxyxohetqwfwnozhjxw.supabase.co"
MEMBERSHIP_SUPABASE_ANON_KEY = "sb_publishable_3gFCaMs17dZJQaJN4DAoeA_3x_q2BWg"

APP_SUPABASE_URL = MEMBERSHIP_SUPABASE_URL
APP_SUPABASE_ANON_KEY = MEMBERSHIP_SUPABASE_ANON_KEY

# Satış / destek. PAYMENT_URL doluysa üyelik ekranında 'Web'den satın al' görünür.
PRICE_TEXT = "Aylık 99,99 TL · Yıllık 999,99 TL"
PAYMENT_URL = ""
SUPPORT_EMAIL = "teknolojimiras@gmail.com"
# GitHub Pages (Settings → Pages → main / docs). Yerel yedek: PRIVACY_POLICY_TR.md
PRIVACY_URL = "https://abdullah-aktas.github.io/nakitce/privacy.html"
