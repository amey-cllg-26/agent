@echo off
title Scholarship Finder Agent
echo ==========================================================
echo       Scholarship Finder Agent - Web Interface
echo ==========================================================
echo.

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Creating virtual environment with Python...
    py -3.13 -m venv .venv
    IF ERRORLEVEL 1 (
        python -m venv .venv
    )
    echo Installing dependencies...
    .venv\Scripts\pip.exe install -r requirements.txt
)

echo Starting Scholarship Finder Web Server on http://127.0.0.1:5000 ...
start http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
pause
