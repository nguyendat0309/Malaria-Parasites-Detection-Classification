@echo off
title Blood Cell Analysis - Setup

echo.
echo ============================================================
echo   Blood Cell Analysis - Setup Wizard
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Starting setup...
echo.

REM Run setup script
python "%~dp0setup_app.py"

echo.
pause
