@echo off
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_apk_build.ps1"
exit /b %ERRORLEVEL%
