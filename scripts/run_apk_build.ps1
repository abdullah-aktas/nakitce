$ErrorActionPreference = "Stop"
$env:TEMP = "D:\tmp-nakitce"
$env:TMP = "D:\tmp-nakitce"
$env:PUB_CACHE = "D:\pub-cache"
$env:GRADLE_USER_HOME = "D:\gradle-home"
$env:ANDROID_HOME = "C:\AndroidSdk"
$env:ANDROID_SDK_ROOT = "C:\AndroidSdk"
$env:PYTHONIOENCODING = "utf-8"
New-Item -ItemType Directory -Force -Path $env:TEMP, $env:PUB_CACHE, $env:GRADLE_USER_HOME | Out-Null
if (Test-Path "C:\fh\flutter") {
    $env:USERPROFILE = "C:\fh"
    $env:HOME = "C:\fh"
}
$src = "D:\Mobil App\Nakitçe"
$dst = "D:\nakitce-build"
robocopy $src $dst /MIR /XD .venv .git .flet build __pycache__ .mypy_cache .ruff_cache .pytest_cache /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
Set-Location $dst
$flet = Join-Path $src ".venv\Scripts\flet.exe"
& $flet build apk --module-name main --yes
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$apk = Get-ChildItem -Path "$dst\build" -Filter "*.apk" -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($apk) {
    $out = Join-Path $src "build\apk"
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    Copy-Item $apk.FullName (Join-Path $out $apk.Name) -Force
    Write-Host "APK_READY=$($apk.FullName)"
}
