# Nakitçe — APK + AAB (Windows)
# Türkçe karakterli proje yolunu ASCII derleme dizinine kopyalar.
#
#   .\scripts\build_android_packages.ps1
#   .\scripts\build_android_packages.ps1 -Targets apk
#   .\scripts\build_android_packages.ps1 -Targets aab,apk
#
# Play imzası (opsiyonel env):
#   FLET_ANDROID_SIGNING_KEY_STORE / _PASSWORD / _KEY_PASSWORD / _ALIAS

param(
    [string]$Targets = "apk,aab",
    [string]$BuildRoot = "D:\nakitce-build"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

chcp 65001 | Out-Null
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

if (-not $env:PUB_CACHE) { $env:PUB_CACHE = "D:\pub-cache" }
if (-not $env:GRADLE_USER_HOME) { $env:GRADLE_USER_HOME = "D:\gradle-home" }
New-Item -ItemType Directory -Force -Path $env:PUB_CACHE, $env:GRADLE_USER_HOME, $BuildRoot | Out-Null

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

Write-Host "==> Sync project -> $BuildRoot (ASCII path for Flutter/Gradle)"
robocopy $ProjectRoot $BuildRoot /MIR /XD .venv .git .flet build __pycache__ .mypy_cache .ruff_cache .pytest_cache node_modules /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit $LASTEXITCODE"
}

Set-Location $BuildRoot

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "==> Export store assets"
    python scripts\export_store_assets.py
}

$targetList = $Targets.Split(",") | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
$results = @()

try {
    foreach ($target in $targetList) {
        if ($target -notin @("apk", "aab")) {
            Write-Warning "Skip unknown target: $target"
            continue
        }
        Write-Host "==> flet build $target"
        flet build $target --module-name main --yes
        $ext = if ($target -eq "apk") { "*.apk" } else { "*.aab" }
        $outDir = Join-Path $BuildRoot "build\$target"
        $artifact = Get-ChildItem -Path $outDir -Filter $ext -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if (-not $artifact) {
            $artifact = Get-ChildItem -Path (Join-Path $BuildRoot "build") -Filter $ext -Recurse -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
        }
        if ($artifact) {
            $destDir = Join-Path $ProjectRoot "build\$target"
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
            $dest = Join-Path $destDir $artifact.Name
            Copy-Item $artifact.FullName $dest -Force
            $mb = [math]::Round((Get-Item $dest).Length / 1MB, 1)
            Write-Host "OK $target -> $dest ($mb MB)"
            $results += $dest
        } else {
            Write-Warning "No $ext produced for $target"
        }
    }
} finally {
    if ($originalProfile) {
        $env:USERPROFILE = $originalProfile
        $env:HOME = $originalProfile
    }
    Set-Location $ProjectRoot
}

Write-Host "==> Done. Artifacts:"
$results | ForEach-Object { Write-Host " - $_" }
if (-not $results) { exit 1 }
