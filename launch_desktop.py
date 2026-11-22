"""
Bypass Browser — Desktop Session Launcher
=========================================
Author: Chirag Chanchal (chiragchanchal2345@gmail.com)
Copyright (c) 2026 Chirag Chanchal | Open Source (MIT)

Launches Bypass Browser directly onto the user's interactive desktop (WinSta0\\default).
"""
import os
import sys
import ctypes
from ctypes import wintypes


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


def launch(target_exe=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if target_exe and os.path.exists(target_exe):
        cmd = f'"{target_exe}"'
        work_dir = os.path.dirname(target_exe)
    else:
        dist_exe = os.path.join(script_dir, "dist", "BypassBrowser", "BypassBrowser.exe")
        if "--exe" in sys.argv and os.path.exists(dist_exe):
            cmd = f'"{dist_exe}"'
            work_dir = os.path.dirname(dist_exe)
        elif len(sys.argv) > 1 and sys.argv[1].endswith(".py") and os.path.exists(sys.argv[1]):
            target_script = os.path.abspath(sys.argv[1])
            python_exe = sys.executable
            cmd = f'"{python_exe}" "{target_script}"'
            work_dir = script_dir
        else:
            browser_py = os.path.join(script_dir, "browser.py")
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(python_exe):
                python_exe = sys.executable
            cmd = f'"{python_exe}" "{browser_py}"'
            work_dir = script_dir

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    si.lpDesktop = "WinSta0\\default"  # Explicitly target interactive desktop
    pi = PROCESS_INFORMATION()

    success = ctypes.windll.kernel32.CreateProcessW(
        None,
        cmd,
        None,
        None,
        False,
        0,
        None,
        work_dir,
        ctypes.byref(si),
        ctypes.byref(pi),
    )

    if success:
        print(f"Browser launched successfully on interactive desktop. PID: {pi.dwProcessId}")
    else:
        err = ctypes.GetLastError()
        print(f"Failed to launch on WinSta0\\default (Error: {err}), falling back...")
        os.system(f'start "" "{python_exe}" "{browser_py}"')


if __name__ == "__main__":
    launch()
