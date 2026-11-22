@echo off
:: ============================================================================
:: Bypass Browser — Privacy & Anti-Fingerprinting Web Browser
:: Author: Chirag Chanchal (chiragchanchal2345@gmail.com)
:: Copyright (c) 2026 Chirag Chanchal | Open Source (MIT)
:: ============================================================================
setlocal
cd /d "%~dp0"
start "" pythonw.exe browser.py %*
if errorlevel 1 (
    echo Launching with standard python...
    python.exe browser.py %*
)
