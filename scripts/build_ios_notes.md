# iOS IPA üretimi

Windows’ta `flet build ipa` **çalışmaz**. Seçenekler:

1. **GitHub Actions** — Actions → `Build iOS IPA` → Run workflow  
   Secrets: `APPLE_TEAM_ID`, `APPLE_CERTIFICATE_BASE64`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_PROVISION_PROFILE_BASE64`
2. **Mac** — Xcode + Flutter + `flet build ipa --module-name main`
3. **Bulut Mac** — MacinCloud vb.

`pyproject.toml` içinde `[tool.flet.ios]` hazır (`com.mirasteknoloji.nakitce`).
