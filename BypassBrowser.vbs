' ============================================================================
' Bypass Browser — Silent Launcher
' Author: Chirag Chanchal (chiragchanchal2345@gmail.com)
' Copyright (c) 2026 Chirag Chanchal | Open Source (MIT)
' ============================================================================
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir
WshShell.Run "pythonw.exe """ & ScriptDir & "\browser.py""", 0, False
