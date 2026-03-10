@echo off
chcp 65001 >nul
setlocal
:: Create symlinks: .cursor/skills and .opencode/skills -> .agents/skills
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

if not exist ".agents\skills" (
    echo [Error] .agents\skills directory not found
    exit /b 1
)

if not exist ".cursor" mkdir ".cursor"
if not exist ".opencode" mkdir ".opencode"

:: Symlinks may require admin or Developer Mode; use mklink /J for junction if needed
if exist ".cursor\skills" (
    echo [Skip] .cursor\skills already exists
) else (
    mklink /J ".cursor\skills" ".agents\skills"
    if errorlevel 1 echo [Note] Run as admin or use junction
)

if exist ".opencode\skills" (
    echo [Skip] .opencode\skills already exists
) else (
    mklink /J ".opencode\skills" ".agents\skills"
    if errorlevel 1 echo [Note] Run as admin or use junction
)

echo Done.
endlocal
