"""
Bypass Browser — Anti-Fingerprinting Zero-Footprint Web Browser
===============================================================
Author: Chirag Chanchal
License: MIT License
Repository: https://github.com/ChiragChanchal/BypassBrowser

Features:
- Instant ephemeral sessions with dedicated isolated temporary sandbox.
- Anti-fingerprint engine randomizing Canvas, WebGL, and Hardware signatures.
- InPrivate RAM-only storage (no persistent cookies, history, or disk cache).
- Complete auto-purge on exit or upon clicking "Fresh Reset".
- Powered by high-performance Microsoft Edge Chromium (WebView2).
"""

import sys
import os
import glob
import shutil
import tempfile
import atexit
import secrets
import random
from urllib.parse import quote_plus

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

# -----------------------------------------------------------------------------
# Application Metadata
# -----------------------------------------------------------------------------
APP_NAME = "Bypass Browser"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Chirag Chanchal"
APP_LICENSE = "MIT License"

# -----------------------------------------------------------------------------
# Ephemeral Session & Cleanup Manager
# -----------------------------------------------------------------------------
TEMP_DIR_PREFIX = "bypass_browser_"
SESSION_DIR = tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX)


def cleanup_session_storage():
    """Wipes all temp session files and cached data from disk on exit."""
    try:
        if os.path.exists(SESSION_DIR):
            shutil.rmtree(SESSION_DIR, ignore_errors=True)
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
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STARTPAGE_PATH = os.path.abspath(os.path.join(BASE_DIR, "startpage", "index.html"))
if os.path.exists(STARTPAGE_PATH):
    STARTPAGE_URI = Uri(STARTPAGE_PATH).AbsoluteUri
else:
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
# URL & Search Helper
# -----------------------------------------------------------------------------
def parse_input_to_uri(text: str) -> str:
    """Parses user input into either a direct URL or a DuckDuckGo search query."""
    text = text.strip()
    if not text:
        return STARTPAGE_URI
    if text.startswith("http://") or text.startswith("https://") or text.startswith("file://"):
        return text
    if "." in text and " " not in text:
        return "https://" + text
    return f"https://duckduckgo.com/?q={quote_plus(text)}"


# -----------------------------------------------------------------------------
# Main Browser Form (Window)
# -----------------------------------------------------------------------------
class BypassBrowserForm(WinForms.Form):
    def __init__(self):
        super().__init__()
        self.Text = f"{APP_NAME} — Anti-Fingerprint & Zero Footprint"
        self.Size = Drawing.Size(1200, 800)
        self.MinimumSize = Drawing.Size(800, 500)
        self.StartPosition = WinForms.FormStartPosition.CenterScreen
        self.BackColor = Drawing.ColorTranslator.FromHtml("#12141a")
        self.KeyPreview = True

        # Generate unique identity for this session
        self.identity = generate_session_identity()

        # Keep track of active tabs and WebView2 instances
        self.tab_map = {}  # TabPage -> WebView2 control

        # Shared InPrivate Creation Properties
        self.creation_props = wf.Chromium.CoreWebView2CreationProperties()
        self.creation_props.UserDataFolder = SESSION_DIR
        self.creation_props.set_IsInPrivateModeEnabled(True)
        self.creation_props.AdditionalBrowserArguments = (
            "--disable-features=ElasticOverscroll "
            "--disable-sync "
            "--no-first-run "
            "--no-default-browser-check "
            "--allow-file-access-from-files"
        )

        self.setup_ui()
        self.KeyDown += self.on_form_key_down
        self.FormClosing += self.on_form_closing
        self.Shown += self.on_form_shown

        # Add initial clean tab
        self.add_tab(STARTPAGE_URI, "Start")

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

        # Fresh Reset Button (instant slate wipe & fingerprint re-seed)
        self.btn_reset = make_btn("🧹 Fresh Reset", "Instant clean slate + New Fingerprint Identity (Ctrl+Shift+Delete)", width=118, bg="#2d3345", fg="#60a5fa")
        self.btn_reset.Font = Drawing.Font("Segoe UI", 9, Drawing.FontStyle.Bold)
        self.btn_reset.Click += lambda s, e: self.instant_fresh_reset()
        self.toolbar.Controls.Add(self.btn_reset)

        # About / Credits Button
        self.btn_about = make_btn("ℹ", "About Bypass Browser & Credits", width=30, bg="#252936", fg="#9ca3af")
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
        tip.SetToolTip(self.lbl_badge, "100% Ephemeral & Anti-Fingerprint Active:\n• InPrivate RAM-only mode\n• Canvas & WebGL signature randomized\n• Zero leftover files on exit\n• Created by Chirag Chanchal")
        self.toolbar.Controls.Add(self.lbl_badge)
        self.Controls.Add(self.toolbar)
        self.toolbar.Resize += self.on_toolbar_resize

        # 2. Bottom Status Bar
        self.status_strip = WinForms.StatusStrip()
        self.status_strip.BackColor = Drawing.ColorTranslator.FromHtml("#161820")
        self.status_label = WinForms.ToolStripStatusLabel()
        self.status_label.Text = f"🔒 Bypass Browser active. Identity: {self.identity['salt'][:8]}..."
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
        self.btn_close_tab.Location = Drawing.Point(self.btn_reset.Left - 40, 8)
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
    # WebView2 Event Handlers
    # -------------------------------------------------------------------------
    def on_wv_ready(self, sender, args, tab_page):
        """Called when CoreWebView2 completes asynchronous initialization."""
        core = sender.CoreWebView2
        if core is None:
            return

        # 1. Disable password and autofill persistence
        try:
            core.Settings.IsPasswordAutosaveEnabled = False
            core.Settings.IsGeneralAutofillEnabled = False
            core.Settings.AreDevToolsEnabled = True
        except Exception:
            pass

        # 2. Inject Anti-Fingerprinting Stealth Script (executes before any page script)
        try:
            stealth_code = build_stealth_script(self.identity)
            core.AddScriptToExecuteOnDocumentCreatedAsync(stealth_code)
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
                self.status_label.Text = f"🔒 Bypass Identity Active ({self.identity['salt'][:8]}...) — 0 traces saved."
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
        # Generate completely new fingerprint
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

    def show_about(self):
        """Displays application credits and open source license information."""
        about_text = (
            f"{APP_NAME} v{APP_VERSION}\n"
            f"Created & Maintained by: {APP_AUTHOR}\n\n"
            f"License: {APP_LICENSE}\n\n"
            "Features:\n"
            "• Zero Persistent Disk Storage (InPrivate RAM-only)\n"
            "• Hardware & Canvas Anti-Fingerprinting Engine\n"
            "• 1-Click Complete Slate Reset (Ctrl+Shift+Delete)\n"
            "• Multi-Tab Browsing & DuckDuckGo Search Integration"
        )
        WinForms.MessageBox.Show(
            about_text,
            f"About {APP_NAME}",
            WinForms.MessageBoxButtons.OK,
            WinForms.MessageBoxIcon.Information,
        )

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


# Backward compatibility alias
FreshBrowserForm = BypassBrowserForm


# -----------------------------------------------------------------------------
# Application Main
# -----------------------------------------------------------------------------
def main():
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


if __name__ == "__main__":
    main()
