# Nakitçe — Google Play AAB build helper (Windows)
#
# Usage (from project root):
#   .\scripts\build_play_aab.ps1
#
# Required for Play upload signing (otherwise debug-signed; Play rejects it):
#   FLET_ANDROID_SIGNING_KEY_STORE
#   FLET_ANDROID_SIGNING_KEY_STORE_PASSWORD
#   FLET_ANDROID_SIGNING_KEY_PASSWORD
# Optional:
#   FLET_ANDROID_SIGNING_KEY_ALIAS   (default: upload)
#
# Path-with-spaces workaround (this machine):
#   mklink /J C:\AndroidSdk "%LOCALAPPDATA%\Android\Sdk"
#   mklink /J C:\fh "%USERPROFILE%"
# Script sets ANDROID_HOME=C:\AndroidSdk and USERPROFILE/HOME=C:\fh for the build.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

chcp 65001 | Out-Null
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Keep Pub/Gradle caches on D: — C: is often full; also avoids C:/D: Kotlin cache bugs.
if (-not $env:PUB_CACHE) { $env:PUB_CACHE = "D:\pub-cache" }
if (-not $env:GRADLE_USER_HOME) { $env:GRADLE_USER_HOME = "D:\gradle-home" }
New-Item -ItemType Directory -Force -Path $env:PUB_CACHE, $env:GRADLE_USER_HOME | Out-Null

# Short junctions avoid NDK/Flutter failures when the Windows username has spaces.
if (Test-Path "C:\AndroidSdk") {
    $env:ANDROID_HOME = "C:\AndroidSdk"
    $env:ANDROID_SDK_ROOT = "C:\AndroidSdk"
} elseif (-not $env:ANDROID_HOME -and (Test-Path "$env:LOCALAPPDATA\Android\Sdk")) {
    $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
    $env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
}

$originalProfile = $env:USERPROFILE
if (Test-Path "C:\fh\flutter") {
    $env:USERPROFILE = "C:\fh"
    $env:HOME = "C:\fh"
    $env:HOMEDRIVE = "C:"
    $env:HOMEPATH = "\fh"
}

Write-Host "==> Exporting Play Store raster assets..."
python scripts\export_store_assets.py

if (-not $env:FLET_ANDROID_SIGNING_KEY_STORE) {
    Write-Warning "No upload keystore env vars — AAB will be debug-signed and cannot be uploaded to Play."
}

if ($env:ANDROID_HOME -match "\s") {
    Write-Warning "ANDROID_HOME contains spaces. Prefer: mklink /J C:\AndroidSdk `"$env:LOCALAPPDATA\Android\Sdk`""
}

Write-Host "==> Building Android App Bundle (AAB)..."
try {
    flet build aab --module-name main --yes
} finally {
    if ($originalProfile) {
        $env:USERPROFILE = $originalProfile
        $env:HOME = $originalProfile
    }
}

$aab = Get-ChildItem -Path "build\aab\*.aab" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $aab) {
    $aab = Get-ChildItem -Path "build" -Filter "*.aab" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if ($aab) {
    $mb = [math]::Round($aab.Length / 1MB, 1)
    Write-Host "AAB ready: $($aab.FullName) ($mb MB)"
    Write-Host "Next: sign with upload keystore if needed, then Play Console > Testing > Internal testing."
} else {
    Write-Host "Build finished but no .aab found under .\build"
}
