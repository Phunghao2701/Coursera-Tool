@echo off
chcp 65001 > nul
setlocal

:: Chuyển đến đúng thư mục chứa file batch này
cd /d "%~dp0"

echo ============================================================
echo             COURSERA BOT - THIẾT LẬP MÔI TRƯỜNG
echo ============================================================
echo.

set PY_CMD=

echo [1/3] Kiểm tra cài đặt Python...

:: Kiểm tra "py"
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :found_python
)

:: Kiểm tra "python"
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :found_python
)

:: Kiểm tra "python3"
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python3
    goto :found_python
)

:: Không tìm thấy Python
echo.
echo [XX] LỖI: Không tìm thấy Python trên máy tính!
echo.
echo Hướng dẫn:
echo   1. Tải Python bản mới nhất tại: https://www.python.org/downloads/
echo   2. Khi cài đặt, NHỚ TÍCH CHỌN: "Add Python to PATH"
echo   3. Sau khi cài xong, mở lại file setup.bat này.
echo.
pause
exit /b 1

:found_python
echo [OK] Tìm thấy Python: 
%PY_CMD% --version

echo.
echo [2/3] Cài đặt các thư viện từ requirements.txt...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt

echo.
echo [3/3] Kiểm tra cấu hình biến môi trường (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" > nul
        echo [OK] Đã tạo file .env từ .env.example.
        echo      👉 Vui lòng mở file .env để điền email, mật khẩu và URL khóa học.
    ) else (
        echo [!] Chưa có .env.example để sao chép.
    )
) else (
    echo [OK] File .env đã tồn tại sẵn.
)

echo.
echo ============================================================
echo   THIẾT LẬP HOÀN TẤT!
echo   1. Mở file .env để kiểm tra/nhập tài khoản Coursera & URL khóa học
echo   2. Double-click file "run_bot.bat" để khởi động bot
echo ============================================================
echo.
pause
