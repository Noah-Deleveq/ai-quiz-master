@echo off
title AI出题官 - 关闭此窗口即停止服务
cd /d "%~dp0"
echo ============================================
echo   AI 出题官  正在启动...
echo   服务地址: http://127.0.0.1:8060
echo   关闭本窗口即可停止服务
echo ============================================
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8060"
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8060
pause
