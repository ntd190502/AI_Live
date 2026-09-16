@echo off
chcp 65001 >nul
title Antigravity Live Gateway Server
echo ========================================================
echo   ANTIGRAVITY LIVE GATEWAY SERVER (CHO APP IOS / TROLLSTORE)
echo ========================================================
echo.
cd /d "%~dp0"
python gateway_server.py --host 0.0.0.0 --port 8000
pause
