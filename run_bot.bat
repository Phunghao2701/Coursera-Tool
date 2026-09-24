@echo off
chcp 65001 > nul
setlocal

:: Chuyển đến đúng thư mục chứa file batch này
cd /d "%~dp0"

echo ============================================================
echo           COURSERA BOT - KHỞI ĐỘNG HỆ THỐNG
echo ============================================================
echo.

set PYTHONUTF8=1

:: 1. Kiểm tra file cấu hình .env
if not exist ".env" (
    echo [!] CHÚ Ý: Chưa tìm thấy file cấu hình .env
    if exist ".env.example" (
        echo [..] Đang tự động tạo file .env từ .env.example...
        copy ".env.example" ".env" > nul
        echo [OK] Đã tạo file .env thành công!
        echo.
        echo 👉 Vui lòng mở file .env để điền tài khoản Coursera và URL khóa học.
        echo    Sau đó chạy lại file run_bot.bat này.
        echo.
        pause
        exit /b 0
    ) else (
        echo [XX] Không tìm thấy cả .env và .env.example!
        pause
        exit /b 1
    )
)

:: 2. Tự động phát hiện môi trường Python (ưu tiên virtualenv nếu có)
set PY_CMD=

if exist ".venv\Scripts\python.exe" (
    set PY_CMD=".venv\Scripts\python.exe"
    goto :run
)

if exist "venv\Scripts\python.exe" (
    set PY_CMD="venv\Scripts\python.exe"
    goto :run
)

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

echo [XX] LỖI: Không tìm thấy Python trong hệ thống!
echo      Vui lòng chạy file setup.bat để thiết lập môi trường.
echo.
pause
exit /b 1

:run
echo [*] Trình thực thi Python: %PY_CMD%
echo.

if exist "main.py" (
    %PY_CMD% main.py
) else (
    %PY_CMD% bot.py
)

echo.
echo ============================================================
echo                  Bot đã kết thúc phiên chạy.
echo ============================================================
pause
