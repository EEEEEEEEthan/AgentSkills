@echo off
chcp 65001 >nul
setlocal
:: Create symlinks: .cursor/skills, .opencode/skills, .claude/skills, .trae/skills -> .agents/skills
:: Only links if parent dir exists; skips if not
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

if not exist ".agents\skills" (
    echo [Error] .agents\skills directory not found
    exit /b 1
)

:: Symlinks may require admin or Developer Mode; use mklink /J for junction if needed
for %%D in (.cursor .opencode .claude .trae) do (
    if exist "%%~D" (
        if exist "%%~D\skills" (
            echo [Skip] %%~D\skills already exists
        ) else (
            mklink /J "%%~D\skills" ".agents\skills"
            if errorlevel 1 echo [Note] Run as admin or use junction
        )
    ) else (
        echo [Skip] %%~D not found
    )
)

echo Done.
pause
endlocal
