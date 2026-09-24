# -*- coding: utf-8 -*-
"""
COURSERA BOT - FASTAPI WEB MONITOR SERVER
=========================================
Cung cấp Web Dashboard, REST API điều khiển Bot (Start/Stop) và WebSocket stream log.
"""

import os
import sys
import asyncio
import secrets
from pathlib import Path
from collections import deque
from typing import Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from utils.logger import log, info, warn, error, success

# Thư mục gốc và thư mục static
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Coursera Bot Dashboard", version="1.0.0")

# Mount thư mục static nếu tồn tại
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

import storage

# ============================================================
#  AUTHENTICATION & SESSION MANAGEMENT
# ============================================================

# Tập hợp các session token hợp lệ
_VALID_TOKENS: Set[str] = set()


class LoginRequest(BaseModel):
    password: str


class SettingsUpdateRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    course_url: Optional[str] = None
    video_speed: Optional[float] = None
    reading_wait: Optional[int] = None
    retry_limit: Optional[int] = None
    discussion_text: Optional[str] = None
    dashboard_password: Optional[str] = None


def get_current_token(request: Request) -> Optional[str]:
    """Lấy token từ Cookie hoặc header Authorization."""
    # 1. Thử cookie
    token = request.cookies.get("session_token")
    if token and token in _VALID_TOKENS:
        return token

    # 2. Thử header Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header.split(" ", 1)[1].strip()
        if bearer_token in _VALID_TOKENS:
            return bearer_token

    return None


def require_auth(token: Optional[str] = Depends(get_current_token)):
    """Dependency bảo vệ các API private."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chưa đăng nhập hoặc phiên làm việc đã hết hạn."
        )
    return token


# ============================================================
#  STATE MANAGER & CONNECTION MANAGER
# ============================================================

class BotStateManager:
    """Quản lý trạng thái và tiến độ bot."""

    def __init__(self):
        self.status: str = "idle"  # idle | running | stopping | error
        self.current_course: str = config.COURSE_URL
        self.current_item_name: str = "Chưa chạy"
        self.current_item_type: str = "N/A"
        self.current_index: int = 0
        self.total_items: int = 0
        self.stats = {
            "reading": {"done": 0, "failed": 0},
            "video": {"done": 0, "failed": 0},
            "discussion": {"done": 0, "failed": 0},
            "graded": {"skipped": 0},
            "unknown": {"skipped": 0},
        }
        self.error_message: Optional[str] = None

    def reset_for_run(self, course_url: str):
        self.status = "running"
        self.current_course = course_url
        self.current_item_name = "Đang khởi tạo trình duyệt..."
        self.current_item_type = "system"
        self.current_index = 0
        self.total_items = 0
        self.stats = {
            "reading": {"done": 0, "failed": 0},
            "video": {"done": 0, "failed": 0},
            "discussion": {"done": 0, "failed": 0},
            "graded": {"skipped": 0},
            "unknown": {"skipped": 0},
        }
        self.error_message = None

    def update_item(self, index: int, total: int, name: str, item_type: str):
        self.current_index = index
        self.total_items = total
        self.current_item_name = name
        self.current_item_type = item_type

    def update_stats(self, stats: dict):
        self.stats = stats

    def set_stopping(self):
        self.status = "stopping"
        self.current_item_name = "Đang ngắt khẩn cấp..."

    def set_idle(self, error_msg: Optional[str] = None):
        self.status = "error" if error_msg else "idle"
        self.error_message = error_msg
        if not error_msg:
            self.current_item_name = "Hoàn thành hoặc đã dừng."

    def get_dict(self) -> dict:
        total_done = (
            self.stats["reading"]["done"]
            + self.stats["video"]["done"]
            + self.stats["discussion"]["done"]
        )
        total_skipped = (
            self.stats["graded"]["skipped"]
            + self.stats["unknown"]["skipped"]
        )
        percent = 0
        if self.total_items > 0:
            percent = round(((self.current_index) / self.total_items) * 100, 1)

        return {
            "status": self.status,
            "course_url": self.current_course,
            "current_item_name": self.current_item_name,
            "current_item_type": self.current_item_type,
            "current_index": self.current_index,
            "total_items": self.total_items,
            "percent": percent,
            "total_done": total_done,
            "total_skipped": total_skipped,
            "stats": self.stats,
            "error_message": self.error_message,
        }


state_manager = BotStateManager()


class ConnectionManager:
    """Quản lý các kết nối WebSocket broadcast log và status."""

    def __init__(self):
        self.log_connections: Set[WebSocket] = set()
        self.status_connections: Set[WebSocket] = set()
        # Lưu buffer chính xác 100 dòng log gần nhất như đã thống nhất
        self.log_buffer: deque = deque(maxlen=100)
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    async def connect_log(self, websocket: WebSocket):
        await websocket.accept()
        self.log_connections.add(websocket)
        # Gửi toàn bộ 100 log đã buffer cho client mới kết nối
        for log_line in self.log_buffer:
            try:
                await websocket.send_text(log_line)
            except Exception:
                pass

    def disconnect_log(self, websocket: WebSocket):
        self.log_connections.discard(websocket)

    async def connect_status(self, websocket: WebSocket):
        await websocket.accept()
        self.status_connections.add(websocket)
        # Gửi ngay trạng thái hiện tại
        try:
            await websocket.send_json(state_manager.get_dict())
        except Exception:
            pass

    def disconnect_status(self, websocket: WebSocket):
        self.status_connections.discard(websocket)

    def broadcast_log_sync(self, message: str):
        """Được gọi từ logging handler đồng bộ trong worker thread."""
        self.log_buffer.append(message)
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast_log_async(message), self.loop)

    async def _broadcast_log_async(self, message: str):
        dead_sockets = []
        for ws in self.log_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.log_connections.discard(ws)

    def broadcast_status_sync(self):
        """Được gọi từ worker thread khi trạng thái thay đổi."""
        if self.loop and self.loop.is_running():
            data = state_manager.get_dict()
            asyncio.run_coroutine_threadsafe(self._broadcast_status_async(data), self.loop)

    async def _broadcast_status_async(self, data: dict):
        dead_sockets = []
        for ws in self.status_connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.status_connections.discard(ws)


ws_manager = ConnectionManager()

# Hook loop khi server khởi động
@app.on_event("startup")
async def on_startup():
    ws_manager.set_loop(asyncio.get_running_loop())
    info(f"Dashboard Web Server sẵn sàng tại cổng {config.DASHBOARD_PORT}")


# ============================================================
#  REST API ENDPOINTS
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Coursera Bot Web Server - Đang chuẩn bị giao diện static...</h1>")


@app.post("/api/login")
async def login(req: LoginRequest, response: Response):
    s = storage.load_settings()
    configured_pwd = s.get("dashboard_password") or config.DASHBOARD_PASSWORD or "coursera123"

    if req.password == configured_pwd:
        token = secrets.token_hex(24)
        _VALID_TOKENS.add(token)
        # Đặt cookie session
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 30  # 30 ngày
        )
        return {"success": True, "token": token, "message": "Đăng nhập thành công!"}
    
    raise HTTPException(status_code=401, detail="Sai mật khẩu bảo vệ Dashboard!")


@app.post("/api/logout")
async def logout(response: Response, token: Optional[str] = Depends(get_current_token)):
    if token in _VALID_TOKENS:
        _VALID_TOKENS.remove(token)
    response.delete_cookie("session_token")
    return {"success": True, "message": "Đã đăng xuất."}


@app.get("/api/status")
async def get_status(token: str = Depends(require_auth)):
    return state_manager.get_dict()


# ============================================================
#  SETTINGS & HISTORY APIS
# ============================================================

@app.get("/api/settings")
async def get_settings(token: str = Depends(require_auth)):
    s = storage.load_settings()
    return {
        "email": s.get("email", ""),
        "password_masked": "******" if s.get("password") else "",
        "course_url": s.get("course_url", ""),
        "video_speed": s.get("video_speed", 2.0),
        "reading_wait": s.get("reading_wait", 35),
        "retry_limit": s.get("retry_limit", 3),
        "discussion_text": s.get("discussion_text", "ok"),
        "dashboard_password_masked": "******" if s.get("dashboard_password") else "",
    }


@app.post("/api/settings")
async def update_settings(req: SettingsUpdateRequest, token: str = Depends(require_auth)):
    update_data = {}
    if req.email is not None and req.email.strip():
        update_data["email"] = req.email.strip()
    if req.password is not None and req.password != "******" and req.password.strip():
        update_data["password"] = req.password.strip()
    if req.course_url is not None and req.course_url.strip():
        update_data["course_url"] = req.course_url.strip()
    if req.video_speed is not None and req.video_speed > 0:
        update_data["video_speed"] = req.video_speed
    if req.reading_wait is not None and req.reading_wait >= 0:
        update_data["reading_wait"] = req.reading_wait
    if req.retry_limit is not None and req.retry_limit >= 0:
        update_data["retry_limit"] = req.retry_limit
    if req.discussion_text is not None:
        update_data["discussion_text"] = req.discussion_text
    if req.dashboard_password is not None and req.dashboard_password != "******" and req.dashboard_password.strip():
        update_data["dashboard_password"] = req.dashboard_password.strip()

    storage.save_settings(update_data)
    return {"success": True, "message": "Đã lưu cấu hình thành công!"}


@app.get("/api/history")
async def get_history(token: str = Depends(require_auth)):
    return storage.load_history()


class StartRequest(BaseModel):
    course_url: Optional[str] = None
    selected_urls: Optional[List[str]] = None



@app.post("/api/start")
async def start_bot(req: StartRequest, token: str = Depends(require_auth)):
    if state_manager.status == "running":
        return JSONResponse(status_code=400, content={"success": False, "message": "Bot đang chạy rồi!"})

    target_url = req.course_url.strip() if req.course_url else config.COURSE_URL
    if not target_url or not target_url.startswith("http"):
        return JSONResponse(status_code=400, content={"success": False, "message": "Vui lòng nhập URL khóa học hợp lệ!"})

    # Khởi chạy bot qua bot_runner
    import bot_runner
    success_started = bot_runner.start(
        course_url=target_url,
        state_mgr=state_manager,
        ws_mgr=ws_manager
    )

    if success_started:
        return {"success": True, "message": "Đã kích hoạt bot!", "state": state_manager.get_dict()}
    return JSONResponse(status_code=500, content={"success": False, "message": "Không thể khởi động bot!"})


@app.post("/api/stop")
async def stop_bot(token: str = Depends(require_auth)):
    if state_manager.status not in ("running", "stopping"):
        return {"success": False, "message": "Bot hiện không chạy."}

    import bot_runner
    bot_runner.emergency_stop()
    return {"success": True, "message": "Đã gửi lệnh ngắt khẩn cấp tới Bot."}


# ============================================================
#  WEBSOCKET ENDPOINTS
# ============================================================

def verify_ws_auth(websocket: WebSocket) -> bool:
    """Kiểm tra token qua cookie hoặc query param trên WebSocket handshake."""
    # 1. Thử cookie
    cookie_token = websocket.cookies.get("session_token")
    if cookie_token and cookie_token in _VALID_TOKENS:
        return True

    # 2. Thử query parameter: ?token=...
    token = websocket.query_params.get("token")
    if token and token in _VALID_TOKENS:
        return True

    return False


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    if not verify_ws_auth(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect_log(websocket)
    try:
        while True:
            # Giữ kết nối mở, client có thể gửi ping
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_log(websocket)
    except Exception:
        ws_manager.disconnect_log(websocket)


@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    if not verify_ws_auth(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect_status(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_status(websocket)
    except Exception:
        ws_manager.disconnect_status(websocket)
