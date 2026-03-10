@echo off
title Blood Cell Analysis

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Run the application
python main.py

REM If error occurred, pause to show message
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
