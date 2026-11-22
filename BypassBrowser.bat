@echo off
setlocal
cd /d "%~dp0"
start "" pythonw.exe browser.py %*
if errorlevel 1 (
    echo Launching with standard python...
    python.exe browser.py %*
)
