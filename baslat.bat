@echo off
chcp 65001 >nul
title İşçi İfade Tutanağı - Yerel
cd /d "%~dp0api"
echo.
echo   İşçi İfade Tutanağı - yerel sunucu
echo   http://127.0.0.1:8000
echo.
start "" http://127.0.0.1:8000
python -m uvicorn index:app --host 127.0.0.1 --port 8000
pause
