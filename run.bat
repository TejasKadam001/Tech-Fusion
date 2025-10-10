@echo off
title Satellite Telemetry Dashboard
color 0a
echo  Satellite Ground Station Dashboard v2.0
echo  =====================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from: https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found - checking version...
python --version

:: Install requirements
echo.
echo [INFO] Installing required packages...
echo This may take a few minutes on first run...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [WARNING] Some packages failed to install
    echo Trying alternative installation...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)

:: Create directories
if not exist "data_log" mkdir data_log
if not exist "templates" mkdir templates
if not exist "static" mkdir static

:: Start the server
echo.
echo [SUCCESS] Starting Ground Station Dashboard...
echo.
echo  Dashboard URL: http://localhost:5501
echo  Network URL:   http://%COMPUTERNAME%:5501
echo.
echo  Press Ctrl+C to stop the server
echo  Close this window to stop the dashboard
echo.
echo [INFO] Server starting...

python app.py

echo.
echo [INFO] Dashboard server stopped.
pause
