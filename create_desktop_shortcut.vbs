' ============================================================================
' Bypass Browser — Desktop Shortcut Script
' Author: Chirag Chanchal (chiragchanchal2345@gmail.com)
' Copyright (c) 2026 Chirag Chanchal | Open Source (MIT)
' ============================================================================
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

DesktopPath = WshShell.SpecialFolders("Desktop")
ShortcutPath = DesktopPath & "\Bypass Browser.lnk"

Set Shortcut = WshShell.CreateShortcut(ShortcutPath)
Shortcut.TargetPath = "wscript.exe"
Shortcut.Arguments = """" & ScriptDir & "\BypassBrowser.vbs"""
Shortcut.WorkingDirectory = ScriptDir
Shortcut.Description = "Bypass Browser — Anti-Fingerprinting Zero-Footprint Web Browser by Chirag Chanchal"
Shortcut.IconLocation = "shell32.dll,220"
Shortcut.Save

WshShell.Popup "Desktop shortcut for Bypass Browser created successfully!", 3, "Bypass Browser", 64
