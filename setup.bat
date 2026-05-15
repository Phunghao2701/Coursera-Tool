@echo off
chcp 65001 > nul
echo ========================================
echo    COURSERA BOT - Cai dat lan dau
echo ========================================
echo.

:: Xac dinh lenh Python co the dung duoc
set PY_CMD=

echo [1/2] Kiem tra Python...

:: Thu "py" truoc (Python Launcher - luon co tren Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    py --version
    goto :found_python
)

:: Thu "python"
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    python --version
    goto :found_python
)

:: Thu "python3"
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python3
    python3 --version
    goto :found_python
)

:: Khong tim thay Python
echo.
echo LOI: Khong tim thay Python!
echo.
echo Cach sua:
echo   1. Tai Python tai: https://www.python.org/downloads/
echo   2. Khi cai, tick chon "Add Python to PATH"
echo   3. Sau khi cai xong, MO LAI cua so CMD moi roi chay lai file nay
echo.
pause
exit /b 1

:found_python
echo Python OK - Dung lenh: %PY_CMD%

echo.
echo [2/2] Cai thu vien can thiet...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install selenium webdriver-manager

:: Luu PY_CMD vao file de run_bot.bat dung
echo %PY_CMD% > py_cmd.txt

echo.
echo ========================================
echo    Cai dat XONG!
echo    Chay bot bang cach double-click run_bot.bat
echo ========================================
pause
