/**
 * COURSERA BOT - DASHBOARD CONTROLLER (app.js)
 * Quản lý trạng thái, kết nối WebSocket và tương tác UI.
 */

// State variables
let sessionToken = localStorage.getItem("session_token") || "";
let logSocket = null;
let statusSocket = null;
let autoScroll = true;
let maxLogLines = 1000;

// DOM Elements
const loginModal = document.getElementById("loginModal");
const loginForm = document.getElementById("loginForm");
const loginPassword = document.getElementById("loginPassword");
const loginError = document.getElementById("loginError");
const logoutBtn = document.getElementById("logoutBtn");

const wsDot = document.getElementById("wsDot");
const wsStatusText = document.getElementById("wsStatusText");
const botStateBadge = document.getElementById("botStateBadge");
const botStateText = document.getElementById("botStateText");

const courseUrlInput = document.getElementById("courseUrlInput");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

const progressPercent = document.getElementById("progressPercent");
const progressCount = document.getElementById("progressCount");
const progressBarFill = document.getElementById("progressBarFill");
const currentItemName = document.getElementById("currentItemName");
const currentItemType = document.getElementById("currentItemType");

const totalDoneCount = document.getElementById("totalDoneCount");
const doneReading = document.getElementById("doneReading");
const doneVideo = document.getElementById("doneVideo");
const doneDiscussion = document.getElementById("doneDiscussion");
const totalSkippedCount = document.getElementById("totalSkippedCount");

const consoleLogs = document.getElementById("consoleLogs");
const toggleScrollBtn = document.getElementById("toggleScrollBtn");
const clearLogsBtn = document.getElementById("clearLogsBtn");


// ============================================================
//  INIT & AUTHENTICATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await checkAuth();
}

async function checkAuth() {
    try {
        const res = await fetch("/api/status", {
            headers: sessionToken ? { "Authorization": `Bearer ${sessionToken}` } : {}
        });

        if (res.status === 401) {
            showLoginModal();
            return;
        }

        if (res.ok) {
            hideLoginModal();
            const data = await res.json();
            updateUIState(data);
            initWebSockets();
        }
    } catch (err) {
        console.error("Lỗi kiểm tra auth:", err);
        showLoginModal();
    }
}

function showLoginModal() {
    loginModal.classList.add("active");
    loginPassword.value = "";
    loginError.textContent = "";
    loginPassword.focus();
}

function hideLoginModal() {
    loginModal.classList.remove("active");
}

function setupEventListeners() {
    // Login form submit
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pwd = loginPassword.value.trim();
        if (!pwd) return;

        loginError.textContent = "";
        try {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: pwd })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                sessionToken = data.token;
                localStorage.setItem("session_token", sessionToken);
                hideLoginModal();
                await checkAuth();
            } else {
                loginError.textContent = data.detail || "Sai mật khẩu!";
            }
        } catch (err) {
            loginError.textContent = "Không thể kết nối máy chủ!";
        }
    });

    // Logout
    logoutBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/logout", { method: "POST" });
        } catch (e) {}
        sessionToken = "";
        localStorage.removeItem("session_token");
        closeWebSockets();
        showLoginModal();
    });

    // Start Bot
    startBtn.addEventListener("click", async () => {
        const url = courseUrlInput.value.trim();
        if (!url) {
            alert("Vui lòng nhập URL khóa học!");
            return;
        }

        startBtn.disabled = true;
        try {
            const res = await fetch("/api/start", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(sessionToken ? { "Authorization": `Bearer ${sessionToken}` } : {})
                },
                body: JSON.stringify({ course_url: url })
            });
            const data = await res.json();
            if (!res.ok) {
                alert(data.message || "Lỗi khi khởi động bot!");
                startBtn.disabled = false;
            }
        } catch (err) {
            alert("Lỗi kết nối khi gửi lệnh Start!");
            startBtn.disabled = false;
        }
    });

    // Stop Bot
    stopBtn.addEventListener("click", async () => {
        if (!confirm("Bạn có chắc chắn muốn ngắt khẩn cấp bot ngay lập tức?")) {
            return;
        }

        stopBtn.disabled = true;
        try {
            const res = await fetch("/api/stop", {
                method: "POST",
                headers: sessionToken ? { "Authorization": `Bearer ${sessionToken}` } : {}
            });
            const data = await res.json();
            if (!res.ok) {
                alert(data.message || "Lỗi khi gửi lệnh Stop!");
            }
        } catch (err) {
            alert("Lỗi kết nối khi gửi lệnh Stop!");
        }
    });

    // Toggle Auto Scroll
    toggleScrollBtn.addEventListener("click", () => {
        autoScroll = !autoScroll;
        toggleScrollBtn.textContent = `Auto-Scroll: ${autoScroll ? "BẬT" : "TẮT"}`;
        toggleScrollBtn.classList.toggle("active", autoScroll);
    });

    // Clear Logs
    clearLogsBtn.addEventListener("click", () => {
        consoleLogs.innerHTML = "";
    });
}


// ============================================================
//  WEBSOCKETS HANDLING
// ============================================================

function initWebSockets() {
    closeWebSockets();

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const host = location.host;
    const tokenQuery = sessionToken ? `?token=${encodeURIComponent(sessionToken)}` : "";

    // 1. Logs WebSocket
    const logUrl = `${protocol}//${host}/ws/logs${tokenQuery}`;
    logSocket = new WebSocket(logUrl);

    logSocket.onopen = () => {
        wsDot.className = "status-dot online";
        wsStatusText.textContent = "Online";
    };

    logSocket.onmessage = (event) => {
        appendLogLine(event.data);
    };

    logSocket.onclose = () => {
        wsDot.className = "status-dot offline";
        wsStatusText.textContent = "Mất kết nối";
        setTimeout(reconnectWebSockets, 2500);
    };

    logSocket.onerror = () => {
        wsDot.className = "status-dot offline";
    };

    // 2. Status WebSocket
    const statusUrl = `${protocol}//${host}/ws/status${tokenQuery}`;
    statusSocket = new WebSocket(statusUrl);

    statusSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateUIState(data);
        } catch (e) {}
    };

    statusSocket.onclose = () => {
        // Will be reconnected by logSocket onclose
    };
}

function closeWebSockets() {
    if (logSocket) {
        logSocket.onclose = null;
        logSocket.close();
        logSocket = null;
    }
    if (statusSocket) {
        statusSocket.onclose = null;
        statusSocket.close();
        statusSocket = null;
    }
}

function reconnectWebSockets() {
    if (!loginModal.classList.contains("active")) {
        console.log("Đang thử kết nối lại WebSocket...");
        initWebSockets();
    }
}


// ============================================================
//  UI UPDATERS
// ============================================================

function updateUIState(state) {
    if (!state) return;

    // 1. Badge trạng thái
    const st = (state.status || "idle").toLowerCase();
    botStateBadge.className = `bot-badge badge-${st}`;
    botStateText.textContent = st.toUpperCase();

    // 2. Nút Start / Stop
    if (st === "running") {
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else if (st === "stopping") {
        startBtn.disabled = true;
        stopBtn.disabled = true;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }

    // 3. URL khóa học
    if (state.course_url && document.activeElement !== courseUrlInput) {
        courseUrlInput.value = state.course_url;
    }

    // 4. Bài học hiện tại
    currentItemName.textContent = state.current_item_name || "Chưa chạy";
    currentItemName.title = state.current_item_name || "";
    currentItemType.textContent = (state.current_item_type || "N/A").toUpperCase();

    // 5. Tiến độ & Thanh tiến trình
    const pct = state.percent || 0;
    progressPercent.textContent = `${pct}%`;
    progressBarFill.style.width = `${pct}%`;
    progressCount.textContent = `${state.current_index || 0} / ${state.total_items || 0} bài`;

    // 6. Số lượng hoàn thành
    totalDoneCount.textContent = state.total_done || 0;
    totalSkippedCount.textContent = state.total_skipped || 0;

    if (state.stats) {
        doneReading.textContent = state.stats.reading?.done || 0;
        doneVideo.textContent = state.stats.video?.done || 0;
        doneDiscussion.textContent = state.stats.discussion?.done || 0;
    }
}

function appendLogLine(rawText) {
    const lineDiv = document.createElement("div");
    lineDiv.className = "log-line";

    // Phân loại màu log
    if (rawText.includes("[OK]")) {
        lineDiv.classList.add("log-ok");
    } else if (rawText.includes("[XX]") || rawText.includes("ERROR")) {
        lineDiv.classList.add("log-err");
    } else if (rawText.includes("[!!]") || rawText.includes("WARN")) {
        lineDiv.classList.add("log-warn");
    } else if (rawText.includes("[>>]")) {
        lineDiv.classList.add("log-step");
    } else if (rawText.includes("[--]")) {
        lineDiv.classList.add("log-skip");
    } else if (rawText.includes("[..]") || rawText.includes("INFO")) {
        lineDiv.classList.add("log-info");
    }

    lineDiv.textContent = rawText;
    consoleLogs.appendChild(lineDiv);

    // Giới hạn số lượng dòng log trên DOM để tránh lag
    while (consoleLogs.childElementCount > maxLogLines) {
        consoleLogs.removeChild(consoleLogs.firstChild);
    }

    // Tự động cuộn xuống cuối
    if (autoScroll) {
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }
}
