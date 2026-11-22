# Bypass Browser

**Bypass Browser** is a minimalist, privacy-first web browser for Windows designed for complete session freshness and anti-fingerprinting protection.

Every time you start the application, it launches into a brand-new, isolated environment with randomized hardware signatures and zero persistent traces on disk.

---

## Author & Credits

- **Creator & Maintainer:** Chirag Chanchal
- **Email:** chiragchanchal2345@gmail.com
- **License:** MIT License

---

## Core Capabilities

- **Zero Disk Persistence:** Browsing history, cookies, and cache reside strictly in memory and are discarded upon exit.
- **Anti-Fingerprint Engine:** Randomizes canvas hashes, WebGL vendor/renderer strings, and hardware concurrency values per session.
- **Extension Mode (Chrome & Firefox):** Install or load extensions directly from unpacked directories, `.crx`, `.xpi`, or `.zip` archives.
- **Security-Audited Architecture:** Strict URL scheme sanitization, disabled host bridging, and credential isolation.
- **Instant Slate Reset:** Click `Fresh Reset` (or press `Ctrl+Shift+Delete`) to generate a new device identity and wipe all active session memory immediately.
- **Clean Interface:** Fast multi-tab browsing, integrated omnibox with DuckDuckGo search, and bundled offline start page.

---

## Extension Mode

Bypass Browser supports loading standard WebExtensions from both Chrome and Firefox:

1. **Toolbar Extension Menu:** Click the puzzle piece (`🧩`) on the toolbar to open the Extension Mode menu:
   - **Load Unpacked Extension (Folder):** Select any directory containing a `manifest.json`.
   - **Install Extension (.crx / .xpi / .zip):** Select a downloaded Chrome `.crx` or Firefox `.xpi` file; the browser automatically extracts and loads it.
   - **Open Extensions Folder:** Opens the local `extensions/` directory in Windows Explorer.
   - **Installed Extensions:** View all active extensions in the current session.
2. **Pre-loading Extensions:** Place unpacked extension folders into the `extensions/` folder next to `BypassBrowser.exe`. Any valid extension is automatically loaded whenever the browser launches.

---

## Security Audit & Hardening

The browser has undergone security hardening to ensure privacy and isolation:

- **Protocol Sanitization:** Strips dangerous pseudo-protocols (`javascript:`, `vbscript:`, `data:text/html`) from the omnibox to prevent script execution vulnerabilities.
- **Host Object & WebMessage Lockdown:** `AreHostObjectsAllowed` and `IsWebMessageEnabled` are disabled, ensuring untrusted web content cannot bridge into host execution contexts.
- **InPrivate Memory Sandbox:** All tabs operate in isolated memory sandboxes with ephemeral profiles. No cookies, browsing logs, or caches persist across runs.
- **Credential Protection:** Autofill and password saving are disabled by default (`IsPasswordAutosaveEnabled = False`).
- **Lock-Resilient Teardown:** The session cleaner uses multi-pass retry logic with exponential backoff to handle transient locks during process termination.

---

## Download & Installation

### Option 1: Pre-built Binary
1. Go to the [Releases](https://github.com/chiragchanchal/Bypass-Browser/releases) page.
2. Download `BypassBrowser-Windows-x64.zip`.
3. Extract the folder and double-click `BypassBrowser.exe` to run.

### Option 2: Running from Source
Ensure Python 3.10+ is installed on Windows:
```powershell
pip install -r requirements.txt
python browser.py
```
Or double-click `BypassBrowser.vbs` for silent launch.

---

## Building the Executable

To build the standalone Windows application from source:
1. Double-click `build_exe.bat` or run:
```powershell
pip install pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name "BypassBrowser" --add-data "startpage;startpage" browser.py
```
The compiled output will be generated inside `dist\BypassBrowser\BypassBrowser.exe`.

---

## Keyboard Shortcuts

- `Ctrl + T`: Open new tab
- `Ctrl + W`: Close current tab
- `Ctrl + L` / `Alt + D`: Focus address bar
- `Ctrl + R` / `F5`: Reload page
- `Alt + Left`: Back
- `Alt + Right`: Forward
- `Ctrl + Shift + Delete`: Fresh Reset (New identity)

---

## License

Copyright (c) 2026 Chirag Chanchal. Open source under the terms of the MIT License.
