@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    python tools\engine_host.py run --editor --path "%CD%"
) else (
    python tools\engine_host.py run %*
)
exit /b %errorlevel%
