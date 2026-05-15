@echo off
chcp 65001 > nul
echo ========================================
echo    COURSERA BOT - Khoi dong...
echo ========================================
echo.

set PYTHONUTF8=1
cd /d "c:\Users\LENOVO\Desktop\tool coursera"

:: --- Tu detect Python (khong dung py_cmd.txt vi co the sai may) ---
set PY_CMD=

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :run
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :run
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python3
    goto :run
)

echo LOI: Khong tim thay Python!
echo Hay chay setup.bat truoc.
pause
exit /b 1

:run
echo Dung lenh Python: %PY_CMD%
echo.
%PY_CMD% bot.py

echo.
echo Bot da ket thuc.
pause
