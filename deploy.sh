#!/usr/bin/env bash
# ============================================================
#  COURSERA BOT - DEPLOY SCRIPT DÀNH CHO LINUX VPS
# ============================================================

set -e

echo "============================================================"
echo "         🚀 COURSERA BOT - TRIỂN KHAI DOCKER TRÊN VPS"
echo "============================================================"
echo ""

# 1. Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "[XX] Docker chưa được cài đặt trên VPS!"
    echo "     Cài đặt nhanh: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# 2. Kiểm tra file .env
if [ ! -f ".env" ]; then
    echo "[!] Chưa tìm thấy file .env"
    if [ -f ".env.example" ]; then
        echo "[..] Đang copy từ .env.example sang .env..."
        cp .env.example .env
        echo "[OK] Đã tạo file .env."
        echo "👉 Vui lòng mở file .env để cấu hình tài khoản trước: nano .env"
        exit 0
    else
        echo "[XX] Không tìm thấy cả .env và .env.example!"
        exit 1
    fi
fi

# 3. Tạo thư mục data nếu chưa có
mkdir -p ./data/chrome-profile ./logs

# 4. Build và khởi chạy Docker Compose
echo "[..] Đang build và khởi động container..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo ""
echo "============================================================"
echo "  🎉 CONTAINER ĐÃ KHỞI ĐỘNG THÀNH CÔNG!"
echo ""
echo "  🌐 Truy cập Web Dashboard tại: http://<IP-VPS>:3987"
echo "  📋 Xem log container:          docker compose logs -f"
echo "  ⏹ Dừng container:             docker compose down"
echo "============================================================"
