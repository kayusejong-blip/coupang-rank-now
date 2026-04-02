@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo "=== 쿠팡 순위 자동 리포터 === "
cd /d "%~dp0"
python auto_reporter.py
