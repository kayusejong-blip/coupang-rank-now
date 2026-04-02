@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo === 쿠팡 랭킹 나우 웹 대시보드를 시작합니다 ===
echo 접속 주소: http://localhost:8000
echo.
timeout /t 1 > nul
start http://localhost:8000
python dashboard/api.py
pause
