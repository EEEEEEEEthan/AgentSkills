@echo off
setlocal
cd /d "%~dp0"

if not "%~1"=="" goto run

for /f "delims=" %%I in ('python .engine_host.py path') do set "engineExe=%%I"
if not defined engineExe exit /b 1
start "" "%engineExe%" --editor --path "%CD%"
exit /b 0

:run
python .engine_host.py run %*
exit /b %errorlevel%
