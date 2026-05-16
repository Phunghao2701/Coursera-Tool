"""
Coursera Bot - Launcher
Giao dien nhap tai khoan va khoa hoc truoc khi chay bot.
"""
import os, sys, json, subprocess, tkinter as tk
from tkinter import ttk, messagebox

os.environ["PYTHONUTF8"] = "1"

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
USER_CFG     = os.path.join(SCRIPT_DIR, "user_config.json")
CONFIG_PY    = os.path.join(SCRIPT_DIR, "config.py")
BOT_PY       = os.path.join(SCRIPT_DIR, "bot.py")

# ---- Load / Save user config ----------------------------------------

def load_cfg() -> dict:
    if os.path.exists(USER_CFG):
        try:
            with open(USER_CFG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cfg(data: dict):
    with open(USER_CFG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_config_py(email, password, course_url, headless=False):
    """Ghi lai config.py voi thong tin moi."""
    headless_val = "True" if headless else "False"
    content = f"""# ============================================================
#  COURSERA BOT - CAU HINH (tu dong tao boi launcher.py)
# ============================================================

# --- Tai khoan Coursera ---
EMAIL    = "{email}"
PASSWORD = "{password}"

# --- Khoa hoc muon chay ---
COURSE_URL = "{course_url}"

# --- Cai dat bot ---
HEADLESS        = {headless_val}   # True = chay ngam, False = hien browser
VIDEO_SPEED     = 2.0     # Toc do video (1.0 = binh thuong, 2.0 = x2)
READING_WAIT    = 35      # Giay doi o trang Reading (Coursera yeu cau 30s)
RETRY_LIMIT     = 3       # So lan thu lai neu khong thay tich xanh
DISCUSSION_TEXT = "ok"    # Noi dung reply o Discussion Prompt

# --- Timeout chung (giay) ---
PAGE_LOAD_TIMEOUT  = 30
ELEMENT_TIMEOUT    = 15
"""
    with open(CONFIG_PY, "w", encoding="utf-8") as f:
        f.write(content)

# ---- GUI ---------------------------------------------------------------

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coursera Bot - Launcher")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Center window
        w, h = 520, 545
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build_ui()
        self._load_saved()

    def _build_ui(self):
        BG     = "#1a1a2e"
        PANEL  = "#16213e"
        ACCENT = "#0f3460"
        BTN    = "#e94560"
        FG     = "#eaeaea"
        LABEL  = "#a0a8c0"

        # Header
        hdr = tk.Frame(self.root, bg=ACCENT, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎓  COURSERA BOT", font=("Segoe UI", 18, "bold"),
                 bg=ACCENT, fg="white").pack()
        tk.Label(hdr, text="Tu dong hoan thanh khoa hoc", font=("Segoe UI", 9),
                 bg=ACCENT, fg="#aac4ff").pack()

        # Form panel
        panel = tk.Frame(self.root, bg=PANEL, padx=30, pady=12)
        panel.pack(fill="both", expand=True, padx=18, pady=18)

        def field(parent, label, show=None):
            tk.Label(parent, text=label, font=("Segoe UI", 9),
                     bg=PANEL, fg=LABEL, anchor="w").pack(fill="x", pady=(6,2))
            entry = tk.Entry(parent, font=("Segoe UI", 11), bg=ACCENT,
                             fg=FG, insertbackground=FG, relief="flat",
                             show=show, bd=0)
            entry.pack(fill="x", ipady=7)
            # Bottom border
            tk.Frame(parent, bg="#334070", height=1).pack(fill="x")
            return entry

        self.email_entry    = field(panel, "📧  Email Coursera")
        self.password_entry = field(panel, "🔒  Mật khẩu", show="•")

        # Show/hide password
        self.show_pass = tk.BooleanVar(value=False)
        tk.Checkbutton(panel, text="Hiện mật khẩu", variable=self.show_pass,
                       command=self._toggle_pass, bg=PANEL, fg=LABEL,
                       activebackground=PANEL, selectcolor=ACCENT,
                       font=("Segoe UI", 8)).pack(anchor="e")

        self.course_entry   = field(panel, "🔗  URL khóa học")
        tk.Label(panel, text="VD: https://www.coursera.org/learn/ten-khoa-hoc/home/welcome",
                 font=("Segoe UI", 7), bg=PANEL, fg="#666e99").pack(anchor="w")

        # Remember checkbox
        self.remember = tk.BooleanVar(value=True)
        tk.Checkbutton(panel, text="Lưu thông tin cho lần sau",
                       variable=self.remember,
                       bg=PANEL, fg=LABEL, activebackground=PANEL,
                       selectcolor=ACCENT, font=("Segoe UI", 8)).pack(anchor="w", pady=(6,0))

        # Headless checkbox
        self.headless = tk.BooleanVar(value=False)
        tk.Checkbutton(panel, text="Chạy ngầm (không hiện browser)",
                       variable=self.headless,
                       bg=PANEL, fg=LABEL, activebackground=PANEL,
                       selectcolor=ACCENT, font=("Segoe UI", 8)).pack(anchor="w", pady=(2,0))

        # Run button
        btn_frame = tk.Frame(self.root, bg=BG, pady=6)
        btn_frame.pack(fill="x", padx=18)

        self.run_btn = tk.Button(
            btn_frame, text="▶   CHẠY BOT",
            font=("Segoe UI", 13, "bold"),
            bg=BTN, fg="white", activebackground="#c73652",
            relief="flat", cursor="hand2", pady=10,
            command=self._on_run
        )
        self.run_btn.pack(fill="x")

        # Footer: status + copyright trong cung 1 frame
        footer = tk.Frame(self.root, bg="#0d0d1a")
        footer.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="San sang.")
        tk.Label(footer, textvariable=self.status_var,
                 font=("Segoe UI", 8), bg="#0d0d1a", fg="#666e99",
                 anchor="w", padx=10, pady=4).pack(side="left")
        tk.Label(footer, text="\u00a9 Distributed by phunghao2701 (https://github.com/phunghao2701)",
                 font=("Segoe UI", 7), bg="#0d0d1a", fg="#4a5280",
                 anchor="e", padx=10).pack(side="right")

    def _toggle_pass(self):
        self.password_entry.config(
            show="" if self.show_pass.get() else "•"
        )

    def _load_saved(self):
        cfg = load_cfg()
        if cfg.get("email"):
            self.email_entry.insert(0, cfg["email"])
        if cfg.get("password"):
            self.password_entry.insert(0, cfg["password"])
        if cfg.get("course_url"):
            self.course_entry.insert(0, cfg["course_url"])
        if cfg.get("headless"):
            self.headless.set(True)

    def _on_run(self):
        email      = self.email_entry.get().strip()
        password   = self.password_entry.get().strip()
        course_url = self.course_entry.get().strip()

        # Validate
        if not email or "@" not in email:
            messagebox.showerror("Lỗi", "Email không hợp lệ!")
            return
        if not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập mật khẩu!")
            return
        if not course_url.startswith("https://www.coursera.org/learn/"):
            messagebox.showerror("Lỗi",
                "URL khóa học không đúng!\n"
                "Phải bắt đầu bằng: https://www.coursera.org/learn/")
            return

        # Luu config
        if self.remember.get():
            save_cfg({"email": email, "password": password,
                      "course_url": course_url, "headless": self.headless.get()})

        # Ghi config.py
        write_config_py(email, password, course_url, headless=self.headless.get())

        self.status_var.set("Đang khởi động bot...")
        self.run_btn.config(state="disabled", text="⏳  Đang chạy...")
        self.root.update()

        # Chay bot.py trong process rieng
        try:
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            subprocess.Popen(
                [sys.executable, BOT_PY],
                cwd=SCRIPT_DIR,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # Mo cua so rieng
            )
            self.status_var.set("Bot đã khởi động! Xem cửa sổ Terminal mới.")
            self.run_btn.config(state="normal", text="▶   CHẠY BOT")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chạy bot:\n{e}")
            self.run_btn.config(state="normal", text="▶   CHẠY BOT")
            self.status_var.set("Lỗi khi khởi động.")


# ---- Entry point -------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()
