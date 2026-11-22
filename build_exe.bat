@echo off
setlocal
echo ========================================================
echo   Building Bypass Browser Executable
echo   Author: Chirag Chanchal
echo ========================================================

cd /d "%~dp0"

echo Installing required packages...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo Compiling executable with PyInstaller...
python -m PyInstaller --noconfirm --onedir --windowed --name "BypassBrowser" --add-data "startpage;startpage" browser.py

if exist "dist\BypassBrowser\startpage" rmdir /s /q "dist\BypassBrowser\startpage"
xcopy /E /I /Y "startpage" "dist\BypassBrowser\startpage"

echo Creating portable zip package...
powershell -Command "Compress-Archive -Path 'dist\BypassBrowser\*' -DestinationPath 'dist\BypassBrowser-Windows-x64.zip' -Force"

echo.
echo Build finished successfully!
echo Executable location: dist\BypassBrowser\BypassBrowser.exe
echo Portable zip package: dist\BypassBrowser-Windows-x64.zip
pause
