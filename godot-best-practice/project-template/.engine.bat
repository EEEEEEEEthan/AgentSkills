@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    python .engine_host.py run --editor --path "%CD%"
) else (
    python .engine_host.py run %*
)
exit /b %errorlevel%
