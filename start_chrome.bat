@echo off
title Khoi dong Google Chrome (CDP Debug Mode 9222)
chcp 65001 >nul

echo ========================================================
echo   DANG TAT TOAN BO TIEN TRINH CHROME DANG CHAY...
echo ========================================================
taskkill /F /IM chrome.exe /T >nul 2>&1
ping 127.0.0.1 -n 3 >nul

echo.
echo ========================================================
echo   DANG KHOI DONG CHROME CHE DO DIEU KHIEN (PORT 9222)...
echo ========================================================

set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

set "USER_DATA_DIR=C:\chrome-debug-profile"

set "TARGET_URL=%~1"
if "%TARGET_URL%"=="" set "TARGET_URL=https://www.youtube.com"

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%USER_DATA_DIR%" --no-first-run "%TARGET_URL%"

echo.
echo [OK] Chrome da mo thanh cong o che do Remote Debugging!
echo Cong ket noi: http://127.0.0.1:9222
ping 127.0.0.1 -n 4 >nul
