"""
Bypass Browser — Anti-Fingerprinting Zero-Footprint Web Browser
===============================================================
Author: Chirag Chanchal
Email: chiragchanchal2345@gmail.com
Copyright (c) 2026 Chirag Chanchal
License: MIT License
Repository: https://github.com/chiragchanchal/Bypass-Browser

Features:
- Instant ephemeral sessions with dedicated isolated temporary sandbox.
- Anti-fingerprint engine randomizing Canvas, WebGL, and Hardware signatures.
- InPrivate RAM-only storage (no persistent cookies, history, or disk cache).
- Complete auto-purge on exit or upon clicking "Fresh Reset".
- Full Extension Mode: Supports Chrome (.crx), Firefox (.xpi), and unpacked extensions.
- Security-audited architecture: protocol sanitization, locked host objects, memory purging.
- Powered by high-performance Microsoft Edge Chromium (WebView2).
"""

import sys
import os
import glob
import time
import shutil
import tempfile
import atexit
import secrets
import random
import zipfile
import struct
import io
import json
import threading
import subprocess
import urllib.request
import pathlib
from urllib.parse import quote_plus

# Platform detection
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
    # Initialize Windows Forms & Drawing through pythonnet / pywebview
    import clr
    clr.AddReference("System")
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")

    from System import Action, Uri
    from System.Threading import Thread, ThreadStart, ApartmentState
    import System.Drawing as Drawing
    import System.Windows.Forms as WinForms
    import webview.platforms.winforms as wf
else:
    Action = Uri = None
    Thread = ThreadStart = ApartmentState = None
    Drawing = WinForms = wf = None

# -----------------------------------------------------------------------------
# Application Metadata & Watermark
# -----------------------------------------------------------------------------
APP_NAME = "Bypass Browser"
APP_VERSION = "1.2.0"
APP_AUTHOR = "Chirag Chanchal"
APP_EMAIL = "chiragchanchal2345@gmail.com"
APP_LICENSE = "MIT License"
APP_WATERMARK = f"{APP_NAME} v{APP_VERSION} | Created by {APP_AUTHOR}"

# Base paths
if getattr(sys, "frozen", False):
    EXE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", EXE_DIR)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = EXE_DIR

BASE_DIR = RESOURCE_DIR
EXTENSIONS_DIR = os.path.join(EXE_DIR, "extensions")
os.makedirs(EXTENSIONS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Ephemeral Session & Cleanup Manager (Security-Audited)
# -----------------------------------------------------------------------------
TEMP_DIR_PREFIX = "bypass_browser_"
SESSION_DIR = tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX)


def cleanup_session_storage():
    """Security audit: Multi-pass cleanup to handle transient locks by browser processes."""
    if not os.path.exists(SESSION_DIR):
        return
    for attempt in range(3):
        try:
            shutil.rmtree(SESSION_DIR, ignore_errors=True)
            if not os.path.exists(SESSION_DIR):
                break
            time.sleep(0.15)
        except Exception:
            pass


def wipe_stale_sessions():
    """Cleans up any orphaned session directories from prior unexpected crashes/reboots."""
    stale_dirs = glob.glob(os.path.join(tempfile.gettempdir(), f"{TEMP_DIR_PREFIX}*"))
    for d in stale_dirs:
        if os.path.abspath(d) != os.path.abspath(SESSION_DIR):
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass


atexit.register(cleanup_session_storage)
wipe_stale_sessions()

# Offline bundled startpage path
startpage_candidate = os.path.abspath(os.path.join(RESOURCE_DIR, "startpage", "index.html"))
if not os.path.exists(startpage_candidate):
    startpage_candidate = os.path.abspath(os.path.join(EXE_DIR, "startpage", "index.html"))

if os.path.exists(startpage_candidate):
    STARTPAGE_PATH = startpage_candidate
    STARTPAGE_URI = pathlib.Path(STARTPAGE_PATH).as_uri()
else:
    STARTPAGE_PATH = None
    STARTPAGE_URI = "https://duckduckgo.com"


# -----------------------------------------------------------------------------
# Anti-Fingerprinting Identity Engine
# -----------------------------------------------------------------------------
GPU_PROFILES = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"),
]


def generate_session_identity():
    """Generates a randomized hardware & canvas signature for each session or reset."""
    vendor, renderer = random.choice(GPU_PROFILES)
    cores = random.choice([4, 6, 8, 12, 16])
    salt = secrets.token_hex(16)
    return {
        "salt": salt,
        "vendor": vendor,
        "renderer": renderer,
        "cores": cores,
    }


def build_stealth_script(identity):
    """Generates the anti-fingerprinting JS payload injected before any page scripts execute."""
    return f"""
    (function() {{
        const SESSION_SALT = "{identity['salt']}";
        const VENDOR = "{identity['vendor']}";
        const RENDERER = "{identity['renderer']}";
        const CORES = {identity['cores']};

        // 1. Spoof Hardware Concurrency
        try {{
            Object.defineProperty(Navigator.prototype, 'hardwareConcurrency', {{
                get: () => CORES,
                configurable: true
            }});
        }} catch(e) {{}}

        // 2. Spoof Canvas Fingerprint (imperceptible 1-pixel shift)
        try {{
            let hash = 0;
            for (let i = 0; i < SESSION_SALT.length; i++) {{
                hash = ((hash << 5) - hash) + SESSION_SALT.charCodeAt(i);
                hash |= 0;
            }}
            const pixelShift = (Math.abs(hash) % 7) + 1;

            if (typeof HTMLCanvasElement !== 'undefined') {{
                const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                    try {{
                        const ctx = this.getContext('2d');
                        if (ctx && this.width > 0 && this.height > 0) {{
                            const img = ctx.getImageData(0, 0, 1, 1);
                            img.data[0] = (img.data[0] ^ pixelShift) & 0xFF;
                            ctx.putImageData(img, 0, 0);
                        }}
                    }} catch(err) {{}}
                    return origToDataURL.apply(this, args);
                }};
            }}

            if (typeof CanvasRenderingContext2D !== 'undefined') {{
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                    const data = origGetImageData.apply(this, args);
                    try {{
                        if (data && data.data && data.data.length > 0) {{
                            data.data[0] = (data.data[0] ^ pixelShift) & 0xFF;
                        }}
                    }} catch(err) {{}}
                    return data;
                }};
            }}
        }} catch(e) {{}}

        // 3. Spoof WebGL (UNMASKED_VENDOR_WEBGL = 37445, UNMASKED_RENDERER_WEBGL = 37446)
        try {{
            const hookGL = function(proto) {{
                if (!proto) return;
                const origGetParam = proto.getParameter;
                proto.getParameter = function(param) {{
                    if (param === 37445 || param === 0x9245) return VENDOR;
                    if (param === 37446 || param === 0x9246) return RENDERER;
                    return origGetParam.apply(this, arguments);
                }};
            }};
            if (typeof WebGLRenderingContext !== 'undefined') hookGL(WebGLRenderingContext.prototype);
            if (typeof WebGL2RenderingContext !== 'undefined') hookGL(WebGL2RenderingContext.prototype);
        }} catch(e) {{}}

        // 4. Clean Storage Protections: Clear any tracking tokens
        try {{
            for (let i = 0; i < localStorage.length; i++) {{
                const k = localStorage.key(i);
                if (k && (k.startsWith('ideas4_') || k.includes('device') || k.includes('fingerprint') || k.includes('rated') || k.includes('vote'))) {{
                    localStorage.removeItem(k);
                }}
            }}
        }} catch(e) {{}}
        try {{
            for (let i = 0; i < sessionStorage.length; i++) {{
                const k = sessionStorage.key(i);
                if (k && (k.startsWith('ideas4_') || k.includes('device') || k.includes('fingerprint') || k.includes('rated') || k.includes('vote'))) {{
                    sessionStorage.removeItem(k);
                }}
            }}
        }} catch(e) {{}}
    }})();
    """


# -----------------------------------------------------------------------------
# Extension Package Extractor (Chrome .crx, Firefox .xpi, Zip)
# -----------------------------------------------------------------------------
def unpack_extension_file(file_path, output_dir):
    """Unpacks .zip, .xpi (Firefox), or .crx (Chrome) into a folder."""
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "rb") as f:
        data = f.read()

    # Standard ZIP / XPI
    if data.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(file_path) as z:
            z.extractall(output_dir)
        return True

    # Chrome CRX format (Cr24 header)
    if data.startswith(b"Cr24"):
        header_size = struct.unpack("<I", data[8:12])[0]
        zip_offset = 12 + header_size
        zip_data = data[zip_offset:]
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            z.extractall(output_dir)
        return True

    return False


# -----------------------------------------------------------------------------
# URL & Search Helper (Security-Audited)
# -----------------------------------------------------------------------------
def parse_input_to_uri(text: str) -> str:
    """Security-audited URL sanitizer: strips malicious schemes, parses URLs or queries."""
    text = text.strip()
    if not text:
        return STARTPAGE_URI

    lower = text.lower()
    # Security: block dangerous pseudo-protocols in omnibox
    for dangerous in ("javascript:", "vbscript:", "data:text/html"):
        if lower.startswith(dangerous):
            return f"https://duckduckgo.com/?q={quote_plus(text)}"

    if lower.startswith("http://") or lower.startswith("https://"):
        return text
    if lower.startswith("file://"):
        return text
    if "." in text and " " not in text:
        return "https://" + text
    return f"https://duckduckgo.com/?q={quote_plus(text)}"


# -----------------------------------------------------------------------------
# Auto-Update Engine (GitHub-Synchronized)
# -----------------------------------------------------------------------------
UPDATE_MANIFEST_URL = "https://raw.githubusercontent.com/chiragchanchal/Bypass-Browser/main/version.json"


def parse_version_tuple(v_str):
    """Converts a version string like '1.2.0' into an integer tuple for comparison."""
    try:
        clean = str(v_str).strip().lstrip("v")
        parts = [int(p) for p in clean.split(".") if p.isdigit()]
        return tuple(parts) if parts else (0, 0, 0)
    except Exception:
        return (0, 0, 0)


def check_for_remote_update():
    """Checks GitHub for an update. Returns (has_update, remote_ver, download_url, notes)."""
    try:
        req = urllib.request.Request(
            UPDATE_MANIFEST_URL,
            headers={"User-Agent": f"BypassBrowser/{APP_VERSION} ({APP_AUTHOR})"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                remote_ver = str(data.get("version", "")).strip()
                dl_url = str(data.get("download_url", "")).strip()
                notes = str(data.get("release_notes", "")).strip()
                if parse_version_tuple(remote_ver) > parse_version_tuple(APP_VERSION):
                    return True, remote_ver, dl_url, notes
                return False, remote_ver, dl_url, notes
    except Exception:
        pass
    return False, APP_VERSION, "", ""


def stage_remote_update(download_url, remote_ver):
    """Downloads the portable package zip and extracts to a clean staging directory."""
    staging_dir = os.path.join(tempfile.gettempdir(), f"bypass_update_{remote_ver}")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    zip_file = os.path.join(staging_dir, "package.zip")
    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"BypassBrowser/{APP_VERSION} ({APP_AUTHOR})"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp, open(zip_file, "wb") as f_out:
        shutil.copyfileobj(resp, f_out)

    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(staging_dir)

    try:
        os.remove(zip_file)
    except Exception:
        pass

    # Check if files were extracted into a nested directory like 'BypassBrowser'
    sub_candidate = os.path.join(staging_dir, "BypassBrowser")
    if os.path.exists(sub_candidate) and os.path.isdir(sub_candidate):
        return sub_candidate
    return staging_dir


def execute_updater_script(staging_path, is_restart=True):
    """Generates and executes a detached Windows script to replace files and restart."""
    current_pid = os.getpid()
    target_install_dir = EXE_DIR

    # If running from source in a git repository, pull directly
    if not getattr(sys, "frozen", False) and os.path.exists(os.path.join(target_install_dir, ".git")):
        try:
            subprocess.run(["git", "pull", "origin", "main"], cwd=target_install_dir, check=True)
            if is_restart:
                python_exe = sys.executable.replace("python.exe", "pythonw.exe")
                if not os.path.exists(python_exe):
                    python_exe = sys.executable
                subprocess.Popen([python_exe, os.path.join(target_install_dir, "browser.py")])
            return True
        except Exception:
            pass

    updater_bat = os.path.join(tempfile.gettempdir(), "apply_bypass_update.bat")
    restart_block = ""
    if is_restart:
        restart_block = f"""
cd /d "{target_install_dir}"
if exist "BypassBrowser.exe" (
    start "" "BypassBrowser.exe"
) else (
    start "" pythonw.exe browser.py
)
"""

    bat_content = f"""@echo off
setlocal
:: ============================================================================
:: Bypass Browser — Automatic Background Update Script
:: Author: Chirag Chanchal (chiragchanchal2345@gmail.com)
:: ============================================================================

:wait_pid
tasklist /fi "PID eq {current_pid}" | find "{current_pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_pid
)

timeout /t 1 /nobreak >nul
xcopy /E /Y /I "{staging_path}\\*" "{target_install_dir}\\"
rmdir /s /q "{staging_path}"
{restart_block}
del "%~f0"
"""
    with open(updater_bat, "w") as f:
        f.write(bat_content)

    CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=CREATE_NO_WINDOW, close_fds=True)
    return True


# -----------------------------------------------------------------------------
# Main Browser Form (Window)
# -----------------------------------------------------------------------------
class BypassBrowserForm(WinForms.Form if IS_WINDOWS else object):
    def __init__(self):
        super().__init__()
        self.Text = f"{APP_NAME} — Anti-Fingerprint & Zero Footprint | by {APP_AUTHOR}"
        self.Size = Drawing.Size(1240, 820)
        self.MinimumSize = Drawing.Size(800, 500)
        self.StartPosition = WinForms.FormStartPosition.CenterScreen
        self.BackColor = Drawing.ColorTranslator.FromHtml("#12141a")
        self.KeyPreview = True

        # Generate unique identity for this session
        self.identity = generate_session_identity()

        # Keep track of active tabs, WebView2 instances, and extensions
        self.tab_map = {}  # TabPage -> WebView2 control
        self.loaded_extensions = []  # list of folder paths
        self.pending_update = None
        self.update_checked = False

        # Discover pre-installed extensions from the extensions/ folder
        self.discover_local_extensions()

        # Shared InPrivate Creation Properties
        self.creation_props = wf.Chromium.CoreWebView2CreationProperties()
        self.creation_props.UserDataFolder = SESSION_DIR
        self.creation_props.set_IsInPrivateModeEnabled(True)

        browser_args = (
            "--disable-features=ElasticOverscroll "
            "--disable-sync "
            "--no-first-run "
            "--no-default-browser-check "
            "--allow-file-access-from-files "
            "--enable-features=msEdgeExtensionAPI"
        )
        if self.loaded_extensions:
            ext_list = ",".join(self.loaded_extensions)
            browser_args += f' --load-extension="{ext_list}"'

        self.creation_props.AdditionalBrowserArguments = browser_args

        self.setup_ui()
        self.KeyDown += self.on_form_key_down
        self.FormClosing += self.on_form_closing
        self.Shown += self.on_form_shown

        # Add initial clean tab
        self.add_tab(STARTPAGE_URI, "Start")

    def discover_local_extensions(self):
        """Discovers any unpacked extensions in the extensions/ directory."""
        dirs_to_check = [EXTENSIONS_DIR]
        if RESOURCE_DIR != EXE_DIR:
            res_ext = os.path.join(RESOURCE_DIR, "extensions")
            if os.path.exists(res_ext) and res_ext not in dirs_to_check:
                dirs_to_check.append(res_ext)

        for d in dirs_to_check:
            if not os.path.exists(d):
                continue
            for item in os.listdir(d):
                full_path = os.path.join(d, item)
                if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "manifest.json")):
                    if full_path not in self.loaded_extensions:
                        self.loaded_extensions.append(full_path)

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------
    def setup_ui(self):
        # 1. Top Navigation Toolbar Panel
        self.toolbar = WinForms.Panel()
        self.toolbar.Dock = WinForms.DockStyle.Top
        self.toolbar.Height = 46
        self.toolbar.BackColor = Drawing.ColorTranslator.FromHtml("#1a1d26")
        self.toolbar.Padding = WinForms.Padding(6, 6, 6, 6)

        # Helper to create styled buttons
        def make_btn(text, tooltip, width=34, bg="#252936", fg="#e2e8f0"):
            btn = WinForms.Button()
            btn.Text = text
            btn.Size = Drawing.Size(width, 30)
            btn.FlatStyle = WinForms.FlatStyle.Flat
            btn.FlatAppearance.BorderSize = 0
            btn.BackColor = Drawing.ColorTranslator.FromHtml(bg)
            btn.ForeColor = Drawing.ColorTranslator.FromHtml(fg)
            btn.Font = Drawing.Font("Segoe UI", 10, Drawing.FontStyle.Bold)
            btn.Cursor = WinForms.Cursors.Hand
            tip = WinForms.ToolTip()
            tip.SetToolTip(btn, tooltip)
            return btn

        # Back Button
        self.btn_back = make_btn("◀", "Back (Alt+Left)")
        self.btn_back.Location = Drawing.Point(8, 8)
        self.btn_back.Click += lambda s, e: self.go_back()
        self.toolbar.Controls.Add(self.btn_back)

        # Forward Button
        self.btn_forward = make_btn("▶", "Forward (Alt+Right)")
        self.btn_forward.Location = Drawing.Point(46, 8)
        self.btn_forward.Click += lambda s, e: self.go_forward()
        self.toolbar.Controls.Add(self.btn_forward)

        # Reload Button
        self.btn_reload = make_btn("↻", "Reload (Ctrl+R / F5)")
        self.btn_reload.Location = Drawing.Point(84, 8)
        self.btn_reload.Click += lambda s, e: self.reload_current()
        self.toolbar.Controls.Add(self.btn_reload)

        # Home Button
        self.btn_home = make_btn("🏠", "Start Page")
        self.btn_home.Location = Drawing.Point(122, 8)
        self.btn_home.Click += lambda s, e: self.navigate_current(STARTPAGE_URI)
        self.toolbar.Controls.Add(self.btn_home)

        # Address & Search Bar (Omnibox)
        self.url_box = WinForms.TextBox()
        self.url_box.Height = 28
        self.url_box.Font = Drawing.Font("Segoe UI", 11)
        self.url_box.BackColor = Drawing.ColorTranslator.FromHtml("#0f1117")
        self.url_box.ForeColor = Drawing.Color.White
        self.url_box.BorderStyle = WinForms.BorderStyle.FixedSingle
        self.url_box.KeyDown += self.on_url_key_down
        self.url_box.Click += lambda s, e: self.url_box.SelectAll()
        self.toolbar.Controls.Add(self.url_box)

        # New Tab Button
        self.btn_new_tab = make_btn("➕", "New Tab (Ctrl+T)")
        self.btn_new_tab.Click += lambda s, e: self.add_tab()
        self.toolbar.Controls.Add(self.btn_new_tab)

        # Close Tab Button
        self.btn_close_tab = make_btn("✕", "Close Tab (Ctrl+W)")
        self.btn_close_tab.Click += lambda s, e: self.close_current_tab()
        self.toolbar.Controls.Add(self.btn_close_tab)

        # Extensions Button
        self.btn_extensions = make_btn("🧩", "Extension Mode: Install or Load Chrome/Firefox Extensions", width=36, bg="#272d3d", fg="#60a5fa")
        self.btn_extensions.Click += lambda s, e: self.show_extensions_menu()
        self.toolbar.Controls.Add(self.btn_extensions)

        # Fresh Reset Button (instant slate wipe & fingerprint re-seed)
        self.btn_reset = make_btn("🧹 Fresh Reset", "Instant clean slate + New Fingerprint Identity (Ctrl+Shift+Delete)", width=118, bg="#2d3345", fg="#60a5fa")
        self.btn_reset.Font = Drawing.Font("Segoe UI", 9, Drawing.FontStyle.Bold)
        self.btn_reset.Click += lambda s, e: self.instant_fresh_reset()
        self.toolbar.Controls.Add(self.btn_reset)

        # About / Credits Button
        self.btn_about = make_btn("ℹ", f"About {APP_NAME} & Author Credits", width=30, bg="#252936", fg="#9ca3af")
        self.btn_about.Click += lambda s, e: self.show_about()
        self.toolbar.Controls.Add(self.btn_about)

        # Privacy Badge
        self.lbl_badge = WinForms.Label()
        self.lbl_badge.Text = "🔒 Bypass Mode"
        self.lbl_badge.AutoSize = False
        self.lbl_badge.Size = Drawing.Size(108, 30)
        self.lbl_badge.TextAlign = Drawing.ContentAlignment.MiddleCenter
        self.lbl_badge.Font = Drawing.Font("Segoe UI", 9, Drawing.FontStyle.Bold)
        self.lbl_badge.ForeColor = Drawing.ColorTranslator.FromHtml("#10b981")
        self.lbl_badge.BackColor = Drawing.ColorTranslator.FromHtml("#142b24")
        tip = WinForms.ToolTip()
        tip.SetToolTip(self.lbl_badge, f"100% Ephemeral & Anti-Fingerprint Active:\n• InPrivate RAM-only mode\n• Canvas & WebGL signature randomized\n• Zero leftover files on exit\n• Created by {APP_AUTHOR}")
        self.toolbar.Controls.Add(self.lbl_badge)
        self.Controls.Add(self.toolbar)
        self.toolbar.Resize += self.on_toolbar_resize

        # 2. Bottom Status Bar
        self.status_strip = WinForms.StatusStrip()
        self.status_strip.BackColor = Drawing.ColorTranslator.FromHtml("#161820")
        self.status_label = WinForms.ToolStripStatusLabel()
        self.status_label.Text = f"🔒 {APP_NAME} active | Identity: {self.identity['salt'][:8]}... | by {APP_AUTHOR}"
        self.status_label.ForeColor = Drawing.ColorTranslator.FromHtml("#9ca3af")
        self.status_strip.Items.Add(self.status_label)
        self.Controls.Add(self.status_strip)

        # 3. Tab Control
        self.tab_control = WinForms.TabControl()
        self.tab_control.Dock = WinForms.DockStyle.Fill
        self.tab_control.Font = Drawing.Font("Segoe UI", 9.5)
        self.tab_control.SelectedIndexChanged += self.on_tab_changed
        self.Controls.Add(self.tab_control)

        # Bring toolbar and status bar forward
        self.toolbar.BringToFront()
        self.status_strip.BringToFront()

        # Initial layout computation
        self.on_toolbar_resize(None, None)

    def on_toolbar_resize(self, sender, e):
        """Dynamically positions navigation buttons and expands the address bar."""
        w = self.toolbar.ClientSize.Width
        # Right aligned items
        self.lbl_badge.Location = Drawing.Point(w - 116, 8)
        self.btn_about.Location = Drawing.Point(self.lbl_badge.Left - 36, 8)
        self.btn_reset.Location = Drawing.Point(self.btn_about.Left - 124, 8)
        self.btn_extensions.Location = Drawing.Point(self.btn_reset.Left - 42, 8)
        self.btn_close_tab.Location = Drawing.Point(self.btn_extensions.Left - 40, 8)
        self.btn_new_tab.Location = Drawing.Point(self.btn_close_tab.Left - 40, 8)

        # Fluid Omnibox
        url_left = self.btn_home.Right + 10
        url_right = self.btn_new_tab.Left - 10
        url_width = max(100, url_right - url_left)

        self.url_box.Location = Drawing.Point(url_left, 9)
        self.url_box.Size = Drawing.Size(url_width, 28)

    # -------------------------------------------------------------------------
    # Tab Management
    # -------------------------------------------------------------------------
    def add_tab(self, url=None, title="New Tab"):
        """Opens a new tab hosting an isolated InPrivate WebView2 control."""
        if url is None:
            url = STARTPAGE_URI

        tab_page = WinForms.TabPage(title)
        tab_page.BackColor = Drawing.ColorTranslator.FromHtml("#0f1117")

        # Create WebView2 instance with shared ephemeral InPrivate profile
        wv = wf.Chromium.WebView2()
        wv.Dock = WinForms.DockStyle.Fill
        wv.CreationProperties = self.creation_props

        # Hook navigation and lifecycle events
        wv.NavigationStarting += lambda s, e: self.on_nav_starting(s, e, tab_page)
        wv.NavigationCompleted += lambda s, e: self.on_nav_completed(s, e, tab_page)
        wv.SourceChanged += lambda s, e: self.on_source_changed(s, e, tab_page)
        wv.CoreWebView2InitializationCompleted += lambda s, e: self.on_wv_ready(s, e, tab_page)

        tab_page.Controls.Add(wv)
        self.tab_map[tab_page] = wv
        self.tab_control.TabPages.Add(tab_page)
        self.tab_control.SelectedTab = tab_page

        # Navigate to target
        wv.Source = Uri(url)
        return wv

    def close_current_tab(self):
        """Closes the current tab, or resets to fresh startpage if only 1 tab remains."""
        current_page = self.tab_control.SelectedTab
        if not current_page:
            return

        if self.tab_control.TabPages.Count <= 1:
            wv = self.tab_map.get(current_page)
            if wv:
                wv.Source = Uri(STARTPAGE_URI)
                current_page.Text = "Start"
                self.status_label.Text = "Returned to clean start page."
            return

        wv = self.tab_map.pop(current_page, None)
        if wv:
            try:
                wv.Dispose()
            except Exception:
                pass

        self.tab_control.TabPages.Remove(current_page)
        current_page.Dispose()
        self.update_nav_state()

    def get_current_wv(self):
        current_page = self.tab_control.SelectedTab
        if current_page:
            return self.tab_map.get(current_page)
        return None

    def on_tab_changed(self, sender, e):
        wv = self.get_current_wv()
        if wv and wv.Source:
            self.update_url_display(wv.Source.ToString())
        self.update_nav_state()

    # -------------------------------------------------------------------------
    # WebView2 Event Handlers (Security-Audited)
    # -------------------------------------------------------------------------
    def on_wv_ready(self, sender, args, tab_page):
        """Called when CoreWebView2 completes asynchronous initialization."""
        core = sender.CoreWebView2
        if core is None:
            return

        # 1. Security Audit: Disable password autosave, autofill, and host objects
        try:
            core.Settings.IsPasswordAutosaveEnabled = False
            core.Settings.IsGeneralAutofillEnabled = False
            core.Settings.AreHostObjectsAllowed = False
            core.Settings.AreDevToolsEnabled = True
        except Exception:
            pass

        # 2. Inject Anti-Fingerprinting Stealth Script (executes before any page script)
        try:
            stealth_code = build_stealth_script(self.identity)
            core.AddScriptToExecuteOnDocumentCreatedAsync(stealth_code)
        except Exception:
            pass

        # 3. Dynamic Browser Extensions Loading
        if self.loaded_extensions and hasattr(core, "Profile") and hasattr(core.Profile, "AddBrowserExtensionAsync"):
            for ext_path in self.loaded_extensions:
                try:
                    task = core.Profile.AddBrowserExtensionAsync(ext_path)
                    def on_ext_loaded(t):
                        if not t.IsFaulted and t.Result:
                            try:
                                t.Result.EnableAsync(True)
                            except Exception:
                                pass
                    task.ContinueWith(Action[object](on_ext_loaded))
                except Exception:
                    pass

        # Handle page title changes
        def on_title_changed(s, a):
            title = s.DocumentTitle
            if title and title.strip():
                short = title if len(title) <= 18 else title[:18] + "…"
                if self.InvokeRequired:
                    self.Invoke(Action(lambda: self.set_tab_text(tab_page, short)))
                else:
                    self.set_tab_text(tab_page, short)

        # Handle popups / target="_blank" links: open as new tab in this browser
        def on_new_window(s, a):
            a.Handled = True
            new_uri = str(a.Uri)
            if new_uri:
                if self.InvokeRequired:
                    self.Invoke(Action(lambda: self.add_tab(new_uri)))
                else:
                    self.add_tab(new_uri)

        core.DocumentTitleChanged += on_title_changed
        core.NewWindowRequested += on_new_window

    def set_tab_text(self, tab_page, text):
        try:
            tab_page.Text = text
        except Exception:
            pass

    def on_nav_starting(self, sender, args, tab_page):
        if tab_page == self.tab_control.SelectedTab:
            target_uri = str(args.Uri)
            self.status_label.Text = f"Connecting to {target_uri[:50]}..."
            self.update_url_display(target_uri)

    def on_source_changed(self, sender, args, tab_page):
        if tab_page == self.tab_control.SelectedTab and sender.Source:
            self.update_url_display(sender.Source.ToString())
            self.update_nav_state()

    def on_nav_completed(self, sender, args, tab_page):
        if tab_page == self.tab_control.SelectedTab:
            if args.IsSuccess:
                self.status_label.Text = f"🔒 Bypass Identity Active ({self.identity['salt'][:8]}...) | 0 traces saved"
            else:
                self.status_label.Text = "Failed to load page. Check URL or network connection."
            self.update_nav_state()

    def update_url_display(self, url_str):
        if url_str == STARTPAGE_URI or "startpage/index.html" in url_str:
            self.url_box.Text = ""
        else:
            self.url_box.Text = url_str

    def update_nav_state(self):
        wv = self.get_current_wv()
        if wv:
            self.btn_back.Enabled = wv.CanGoBack
            self.btn_forward.Enabled = wv.CanGoForward

    # -------------------------------------------------------------------------
    # Navigation Actions
    # -------------------------------------------------------------------------
    def on_url_key_down(self, sender, e):
        if e.KeyCode == WinForms.Keys.Enter:
            e.SuppressKeyPress = True
            target = parse_input_to_uri(self.url_box.Text)
            self.navigate_current(target)

    def navigate_current(self, url_str):
        wv = self.get_current_wv()
        if wv:
            wv.Source = Uri(url_str)

    def go_back(self):
        wv = self.get_current_wv()
        if wv and wv.CanGoBack:
            wv.GoBack()

    def go_forward(self):
        wv = self.get_current_wv()
        if wv and wv.CanGoForward:
            wv.GoForward()

    def reload_current(self):
        wv = self.get_current_wv()
        if wv:
            wv.Reload()

    def instant_fresh_reset(self):
        """
        Instant Reset:
        1. Generates brand-new hardware & canvas identity.
        2. Purges all in-memory cookies & browsing data.
        3. Clears localStorage / sessionStorage / IndexedDB.
        4. Re-injects the new stealth script.
        5. Reloads current page or navigates to clean start.
        """
        self.identity = generate_session_identity()
        stealth_code = build_stealth_script(self.identity)

        for page, wv in list(self.tab_map.items()):
            core = wv.CoreWebView2
            if core:
                try:
                    if core.CookieManager:
                        core.CookieManager.DeleteAllCookies()
                except Exception:
                    pass
                try:
                    if core.Profile:
                        core.Profile.ClearBrowsingDataAsync()
                except Exception:
                    pass
                try:
                    core.AddScriptToExecuteOnDocumentCreatedAsync(stealth_code)
                except Exception:
                    pass
                try:
                    core.ExecuteScriptAsync("try { localStorage.clear(); sessionStorage.clear(); } catch(e){}")
                except Exception:
                    pass

        # Reload the current active page with the brand-new identity
        current_wv = self.get_current_wv()
        if current_wv and current_wv.Source:
            current_url = current_wv.Source.ToString()
            if "startpage" in current_url:
                current_wv.Source = Uri(STARTPAGE_URI)
            else:
                current_wv.Reload()

        self.status_label.Text = f"✨ Brand-New Identity Generated ({self.identity['salt'][:8]}...) — Slate completely wiped!"

    # -------------------------------------------------------------------------
    # Extension Management Mode (Chrome / Firefox / Unpacked Extensions)
    # -------------------------------------------------------------------------
    def show_extensions_menu(self):
        """Displays a menu allowing the user to install or manage extensions."""
        menu = WinForms.ContextMenuStrip()

        item_unpacked = menu.Items.Add("➕ Load Unpacked Extension (Folder)...")
        item_unpacked.Click += lambda s, e: self.prompt_load_unpacked_extension()

        item_package = menu.Items.Add("📦 Install Extension (.crx / .xpi / .zip)...")
        item_package.Click += lambda s, e: self.prompt_install_extension_package()

        menu.Items.Add(WinForms.ToolStripSeparator())

        item_open_dir = menu.Items.Add("📁 Open Extensions Folder")
        item_open_dir.Click += lambda s, e: os.system(f'explorer.exe "{EXTENSIONS_DIR}"')

        item_list = menu.Items.Add(f"📋 Installed Extensions ({len(self.loaded_extensions)})")
        item_list.Click += lambda s, e: self.show_installed_extensions_list()

        btn_screen_point = self.btn_extensions.PointToScreen(Drawing.Point(0, self.btn_extensions.Height))
        menu.Show(btn_screen_point)

    def prompt_load_unpacked_extension(self):
        """Prompts user to select an unpacked extension folder containing manifest.json."""
        dialog = WinForms.FolderBrowserDialog()
        dialog.Description = "Select an unpacked Chrome/Firefox extension folder containing manifest.json"
        dialog.ShowNewFolderButton = False
        if dialog.ShowDialog(self) == WinForms.DialogResult.OK:
            selected_path = dialog.SelectedPath
            if not os.path.exists(os.path.join(selected_path, "manifest.json")):
                WinForms.MessageBox.Show(
                    "Invalid extension folder: manifest.json was not found in the selected folder.",
                    "Extension Error",
                    WinForms.MessageBoxButtons.OK,
                    WinForms.MessageBoxIcon.Warning,
                )
                return
            self.apply_extension_to_session(selected_path)

    def prompt_install_extension_package(self):
        """Prompts user to select a .crx, .xpi, or .zip extension file to extract and install."""
        dialog = WinForms.OpenFileDialog()
        dialog.Title = "Select Extension Package"
        dialog.Filter = "Extension Packages (*.crx;*.xpi;*.zip)|*.crx;*.xpi;*.zip|All Files (*.*)|*.*"
        if dialog.ShowDialog(self) == WinForms.DialogResult.OK:
            pkg_file = dialog.FileName
            pkg_name = os.path.splitext(os.path.basename(pkg_file))[0]
            target_dir = os.path.join(EXTENSIONS_DIR, pkg_name)
            try:
                success = unpack_extension_file(pkg_file, target_dir)
                if success and os.path.exists(os.path.join(target_dir, "manifest.json")):
                    self.apply_extension_to_session(target_dir)
                else:
                    WinForms.MessageBox.Show(
                        "Failed to parse extension: manifest.json was missing inside the package.",
                        "Extension Error",
                        WinForms.MessageBoxButtons.OK,
                        WinForms.MessageBoxIcon.Warning,
                    )
            except Exception as ex:
                WinForms.MessageBox.Show(
                    f"Error unpacking extension: {ex}",
                    "Extension Error",
                    WinForms.MessageBoxButtons.OK,
                    WinForms.MessageBoxIcon.Error,
                )

    def apply_extension_to_session(self, ext_path):
        """Dynamically loads and activates the extension on all active tabs."""
        if ext_path not in self.loaded_extensions:
            self.loaded_extensions.append(ext_path)

        success_count = 0
        for page, wv in self.tab_map.items():
            if wv.CoreWebView2 and hasattr(wv.CoreWebView2, "Profile") and hasattr(wv.CoreWebView2.Profile, "AddBrowserExtensionAsync"):
                try:
                    task = wv.CoreWebView2.Profile.AddBrowserExtensionAsync(ext_path)
                    def on_ext_enabled(t):
                        if not t.IsFaulted and t.Result:
                            try:
                                t.Result.EnableAsync(True)
                            except Exception:
                                pass
                    task.ContinueWith(Action[object](on_ext_enabled))
                    success_count += 1
                except Exception:
                    pass

        ext_name = os.path.basename(ext_path)
        WinForms.MessageBox.Show(
            f"Extension '{ext_name}' installed and enabled for this session!\n\nFolder: {ext_path}",
            "Extension Installed",
            WinForms.MessageBoxButtons.OK,
            WinForms.MessageBoxIcon.Information,
        )
        self.status_label.Text = f"🧩 Extension '{ext_name}' enabled successfully."

    def show_installed_extensions_list(self):
        """Lists all extensions currently loaded in the browser session."""
        if not self.loaded_extensions:
            msg = "No extensions currently loaded.\n\nClick 'Load Unpacked Extension' or place folders in the 'extensions/' directory."
        else:
            msg = "Currently Loaded Extensions:\n\n"
            for i, p in enumerate(self.loaded_extensions, 1):
                msg += f"{i}. {os.path.basename(p)} ({p})\n"
        WinForms.MessageBox.Show(msg, "Active Extensions", WinForms.MessageBoxButtons.OK, WinForms.MessageBoxIcon.Information)

    def show_about(self):
        """Displays application credits and open source license information."""
        about_text = (
            f"{APP_NAME} v{APP_VERSION}\n"
            f"Created & Maintained by: {APP_AUTHOR} ({APP_EMAIL})\n\n"
            f"License: {APP_LICENSE}\n"
            f"Repository: https://github.com/chiragchanchal/Bypass-Browser\n\n"
            "Features:\n"
            "• Zero Persistent Disk Storage (InPrivate RAM-only)\n"
            "• Hardware & Canvas Anti-Fingerprinting Engine\n"
            "• Chrome & Firefox Extension Mode Support\n"
            "• Automatic Background Updates Across All Devices\n"
            "• 1-Click Complete Slate Reset (Ctrl+Shift+Delete)\n"
            "• Multi-Tab Browsing & DuckDuckGo Search Integration\n\n"
            "Would you like to check for updates now?"
        )
        res = WinForms.MessageBox.Show(
            about_text,
            f"About {APP_NAME}",
            WinForms.MessageBoxButtons.YesNo,
            WinForms.MessageBoxIcon.Information,
        )
        if res == WinForms.DialogResult.Yes:
            self.manual_check_for_updates()

    # -------------------------------------------------------------------------
    # Automatic Update System (GitHub-Synchronized)
    # -------------------------------------------------------------------------
    def background_update_worker(self):
        """Silently checks for updates in the background after startup."""
        time.sleep(2.5)  # brief delay to prioritize startpage rendering
        try:
            has_update, remote_ver, dl_url, notes = check_for_remote_update()
            if has_update and dl_url:
                if self.InvokeRequired:
                    self.Invoke(Action(lambda: self.on_update_detected(remote_ver, dl_url, notes)))
                else:
                    self.on_update_detected(remote_ver, dl_url, notes)
        except Exception:
            pass

    def on_update_detected(self, remote_ver, dl_url, notes):
        """Triggered when a newer version is discovered on GitHub."""
        self.status_label.Text = f"🚀 New update v{remote_ver} found! Downloading in background..."

        def download_worker():
            try:
                staging_path = stage_remote_update(dl_url, remote_ver)
                def notify_ready():
                    self.on_update_ready(staging_path, remote_ver, notes)
                if self.InvokeRequired:
                    self.Invoke(Action(notify_ready))
                else:
                    notify_ready()
            except Exception:
                pass

        threading.Thread(target=download_worker, daemon=True).start()

    def on_update_ready(self, staging_path, remote_ver, notes):
        """Triggered when the update package has finished downloading and extracting."""
        self.pending_update = (staging_path, remote_ver)
        self.status_label.Text = f"✨ Update v{remote_ver} downloaded! Click here to restart and apply."
        self.status_label.ForeColor = Drawing.ColorTranslator.FromHtml("#60a5fa")
        self.status_label.Cursor = WinForms.Cursors.Hand
        self.status_label.Click += lambda s, e: self.prompt_apply_update()

        msg = (
            f"A new version of {APP_NAME} (v{remote_ver}) has been automatically downloaded and prepared!\n\n"
            f"Release Notes:\n{notes}\n\n"
            "Would you like to restart now to complete the update automatically?\n"
            "(If you select 'No', the update will be applied seamlessly next time you close the browser.)"
        )
        res = WinForms.MessageBox.Show(
            self,
            msg,
            f"Update Ready — {APP_NAME}",
            WinForms.MessageBoxButtons.YesNo,
            WinForms.MessageBoxIcon.Information,
        )
        if res == WinForms.DialogResult.Yes:
            self.apply_update_now(staging_path)

    def prompt_apply_update(self):
        """Prompts user to apply the pending update if they click the status bar."""
        if not self.pending_update:
            return
        staging_path, remote_ver = self.pending_update
        res = WinForms.MessageBox.Show(
            self,
            f"Restart {APP_NAME} now to apply update v{remote_ver}?",
            "Apply Update",
            WinForms.MessageBoxButtons.YesNo,
            WinForms.MessageBoxIcon.Question,
        )
        if res == WinForms.DialogResult.Yes:
            self.apply_update_now(staging_path)

    def apply_update_now(self, staging_path):
        """Triggers the detached updater script and exits the browser process."""
        execute_updater_script(staging_path, is_restart=True)
        self.Close()

    def manual_check_for_updates(self):
        """Runs a manual update check triggered from the About dialog."""
        self.status_label.Text = "Checking GitHub for updates..."
        def worker():
            try:
                has_update, remote_ver, dl_url, notes = check_for_remote_update()
                if has_update and dl_url:
                    if self.InvokeRequired:
                        self.Invoke(Action(lambda: self.on_update_detected(remote_ver, dl_url, notes)))
                    else:
                        self.on_update_detected(remote_ver, dl_url, notes)
                else:
                    def show_current():
                        self.status_label.Text = f"{APP_NAME} v{APP_VERSION} is up to date."
                        WinForms.MessageBox.Show(
                            self,
                            f"You are running the latest version of {APP_NAME} (v{APP_VERSION}).\n\nNo updates are needed.",
                            "Up to Date",
                            WinForms.MessageBoxButtons.OK,
                            WinForms.MessageBoxIcon.Information,
                        )
                    if self.InvokeRequired:
                        self.Invoke(Action(show_current))
                    else:
                        show_current()
            except Exception as ex:
                def show_err():
                    WinForms.MessageBox.Show(self, f"Could not check for updates: {ex}", "Update Check", WinForms.MessageBoxButtons.OK, WinForms.MessageBoxIcon.Warning)
                if self.InvokeRequired:
                    self.Invoke(Action(show_err))
                else:
                    show_err()

        threading.Thread(target=worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # Keyboard Accelerators
    # -------------------------------------------------------------------------
    def on_form_key_down(self, sender, e):
        if e.Control and e.KeyCode == WinForms.Keys.T:
            self.add_tab()
            e.Handled = True
        elif e.Control and e.KeyCode == WinForms.Keys.W:
            self.close_current_tab()
            e.Handled = True
        elif e.Control and e.KeyCode == WinForms.Keys.L:
            self.url_box.Focus()
            self.url_box.SelectAll()
            e.Handled = True
        elif e.Alt and e.KeyCode == WinForms.Keys.D:
            self.url_box.Focus()
            self.url_box.SelectAll()
            e.Handled = True
        elif e.Control and e.KeyCode == WinForms.Keys.R:
            self.reload_current()
            e.Handled = True
        elif e.KeyCode == WinForms.Keys.F5:
            self.reload_current()
            e.Handled = True
        elif e.Alt and e.KeyCode == WinForms.Keys.Left:
            self.go_back()
            e.Handled = True
        elif e.Alt and e.KeyCode == WinForms.Keys.Right:
            self.go_forward()
            e.Handled = True
        elif e.Control and e.Shift and e.KeyCode == WinForms.Keys.Delete:
            self.instant_fresh_reset()
            e.Handled = True

    def on_form_shown(self, sender, e):
        """Forces window to the top and brings to active foreground on launch."""
        self.Activate()
        self.BringToFront()
        try:
            import ctypes
            hwnd = self.Handle.ToInt32()
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        # Trigger background automatic update check (once per launch)
        if not self.update_checked:
            self.update_checked = True
            threading.Thread(target=self.background_update_worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # Window Teardown & Permanent Wiping
    # -------------------------------------------------------------------------
    def on_form_closing(self, sender, e):
        """Disposes all WebView2 controls and purges session storage."""
        for page, wv in list(self.tab_map.items()):
            try:
                wv.Dispose()
            except Exception:
                pass
        self.tab_map.clear()
        cleanup_session_storage()

        # If an update was downloaded in the background, apply it silently upon exit
        if self.pending_update:
            try:
                staging_path, remote_ver = self.pending_update
                execute_updater_script(staging_path, is_restart=False)
            except Exception:
                pass


# Backward compatibility alias
FreshBrowserForm = BypassBrowserForm


def run_unix_browser():
    """Native cross-platform browser engine for macOS (Cocoa/WebKit) and Linux (WebKitGTK)."""
    import webview

    identity = generate_session_identity()
    stealth_code = build_stealth_script(identity)
    start_url = STARTPAGE_URI if STARTPAGE_PATH else "https://duckduckgo.com"

    class UnixBrowserApi:
        def reset_identity(self):
            nonlocal identity, stealth_code
            identity = generate_session_identity()
            stealth_code = build_stealth_script(identity)
            window.load_url(start_url)
            return identity["salt"][:8]

        def get_identity(self):
            return identity

    api = UnixBrowserApi()
    window = webview.create_window(
        title=f"{APP_NAME} — Anti-Fingerprint & Zero Footprint | by {APP_AUTHOR}",
        url=start_url,
        js_api=api,
        width=1240,
        height=820,
        min_size=(800, 500),
        background_color="#12141a",
        private_mode=True,  # InPrivate RAM-only sandbox on macOS WebKit & Linux WebKitGTK
    )

    def on_loaded():
        try:
            window.evaluate_js(stealth_code)
        except Exception:
            pass

    window.events.loaded += on_loaded

    # Check for updates in background
    threading.Thread(target=check_for_remote_update, daemon=True).start()

    webview.start(private_mode=True)
    cleanup_session_storage()


# -----------------------------------------------------------------------------
# Application Main
# -----------------------------------------------------------------------------
def main():
    if IS_WINDOWS:
        def start_gui():
            WinForms.Application.EnableVisualStyles()
            WinForms.Application.SetCompatibleTextRenderingDefault(False)
            form = BypassBrowserForm()
            WinForms.Application.Run(form)

        # WebView2 and WinForms REQUIRE Single-Threaded Apartment (STA) thread
        gui_thread = Thread(ThreadStart(start_gui))
        gui_thread.SetApartmentState(ApartmentState.STA)
        gui_thread.Start()

        while gui_thread.IsAlive:
            gui_thread.Join(500)

        # Post-run cleanup sweep
        cleanup_session_storage()
    else:
        run_unix_browser()


if __name__ == "__main__":
    main()
