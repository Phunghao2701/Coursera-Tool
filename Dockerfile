# ============================================================
# COURSERA AUTO BOT - DOCKERFILE
# Chạy Chrome Headless + FastAPI Web Dashboard trên VPS 24/7
# ============================================================

FROM python:3.11-slim-bookworm

# Ngăn prompt tương tác khi apt install
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    HEADLESS=true \
    DASHBOARD_PORT=3987 \
    CHROME_USER_DATA_DIR=/app/data/chrome-profile

WORKDIR /app

# 1. Cài đặt Chromium, Chromium-Driver và dumb-init để dọn tiến trình con
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    curl \
    ca-certificates \
    dumb-init \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Tạo các thư mục lưu trữ profile và logs
RUN mkdir -p /app/data/chrome-profile /app/logs /tmp/cache

# 4. Sao chép mã nguồn ứng dụng
COPY config.py .
COPY bot.py .
COPY bot_runner.py .
COPY server.py .
COPY main.py .
COPY handlers/ ./handlers/
COPY utils/ ./utils/
COPY static/ ./static/

# Mở cổng Dashboard (port 3987 theo cấu hình)
EXPOSE 3987

# Sử dụng dumb-init làm PID 1 để bắt và forward signals (SIGINT, SIGTERM) chuẩn xác
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Khởi động Web Server FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3987"]
