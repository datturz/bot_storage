@echo off
REM Discord Clan Storage Bot - Windows Startup Script
REM Handles UTF-8 encoding for proper emoji display

echo Starting Discord Clan Storage Bot...
echo.

REM Set console to UTF-8 mode
chcp 65001 >nul 2>&1

REM Set environment variables for Python UTF-8 support
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSFSENCODING=utf-8

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update requirements if needed
if exist "requirements.txt" (
    echo Checking dependencies...
    pip install -r requirements.txt --quiet
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Creating from template...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Please edit .env file with your configuration before running again.
        pause
        exit /b 1
    ) else (
        echo Error: Neither .env nor .env.example found.
        pause
        exit /b 1
    )
)

REM Check if Google credentials exist
if not exist "credentials\google_service_account.json" (
    echo Warning: Google credentials not found at credentials\google_service_account.json
    echo Please place your Google service account JSON file there.
    pause
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "credentials" mkdir credentials

echo.
echo Starting bot with UTF-8 encoding support...
echo Press Ctrl+C to stop the bot
echo.

REM Run the bot
python main.py

REM Handle exit
if %ERRORLEVEL% equ 0 (
    echo Bot exited normally.
) else (
    echo Bot exited with error code: %ERRORLEVEL%
)

echo.
pause