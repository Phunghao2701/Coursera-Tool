@echo off
chcp 65001 > nul
echo ========================================
echo    COURSERA BOT - Khoi dong...
echo ========================================
echo.

set PYTHONUTF8=1
cd /d "c:\Users\LENOVO\Desktop\tool coursera"

:: Xac dinh lenh Python
set PY_CMD=

:: Doc tu file da luu khi setup (neu co)
if exist py_cmd.txt (
    set /p PY_CMD=<py_cmd.txt
    :: Xoa khoang trang thua
    for /f "tokens=* delims= " %%a in ("%PY_CMD%") do set PY_CMD=%%a
)

:: Neu chua co hoac file khong ton tai, tu detect
if "%PY_CMD%"=="" (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set PY_CMD=py
)
if "%PY_CMD%"=="" (
    python --version >nul 2>&1
    if %errorlevel% equ 0 set PY_CMD=python
)
if "%PY_CMD%"=="" (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 set PY_CMD=python3
)

if "%PY_CMD%"=="" (
    echo LOI: Khong tim thay Python!
    echo Hay chay setup.bat truoc.
    pause
    exit /b 1
)

echo Dung lenh Python: %PY_CMD%
echo.
%PY_CMD% bot.py

echo.
echo Bot da ket thuc.
pause
