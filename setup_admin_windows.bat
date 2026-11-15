@echo off
cd /d "%~dp0"
echo.
echo AAIAP - create / change admin photo password
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 setup_admin.py
) else (
    python setup_admin.py
)
pause
