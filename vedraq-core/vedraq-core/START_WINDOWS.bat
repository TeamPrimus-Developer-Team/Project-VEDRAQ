@echo off
title LIFELINE — Humanitarian Intelligence Platform

echo.
echo  ====================================================
echo   LIFELINE — Humanitarian Intelligence Platform
echo   Smart India Hackathon Demo
echo  ====================================================
echo.

:: Step 1 - Check Python
echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.13 from python.org
    pause
    exit /b 1
)

:: Step 2 - Create venv
if not exist "backend\.venv" (
    echo [2/4] Creating virtual environment...
    python -m venv backend\.venv
) else (
    echo [2/4] Virtual environment exists, skipping...
)

:: Step 3 - Install deps
echo [3/4] Installing dependencies...
backend\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

:: Step 4 - Start server
echo [4/4] Starting server...
echo.
echo  Dashboard : http://0.0.0.0:8001
echo  API Docs  : http://0.0.0.0:8001/docs
echo  Press Ctrl+C to stop
echo.

set PYTHONPATH=backend
backend\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload --app-dir backend
pause
