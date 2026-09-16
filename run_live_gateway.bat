@echo off
title ANTIGRAVITY LIVE GATEWAY (PORT 8000)
chcp 65001 >nul
cd /d "%~dp0"
color 0B

echo ======================================================================
echo      ANTIGRAVITY AI LIVE VOICE GATEWAY - DESKTOP INTERACTIVE MODE
echo ======================================================================
echo.
echo [*] Thu muc lam viec: %CD%
echo [*] Kiem tra giai phong cong 8000 cu neu co...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [*] Phat hien tien trinh PID %%a dang chiem port 8000, dang tat...
    taskkill /F /PID %%a >nul 2>&1
)
echo.
echo [*] Dang khoi dong Gateway Server tren man hinh that...
echo [*] Cong ket noi: http://0.0.0.0:8000
echo [*] Live WebSocket: ws://0.0.0.0:8000/ws/live
echo.
echo [LUU Y] Giu cua so nay de iPhone ket noi va Chrome hien thi tren man hinh!
echo ======================================================================
echo.

python gateway_server.py --host 0.0.0.0 --port 8000
pause
