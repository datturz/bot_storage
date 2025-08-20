# Discord Clan Storage Bot - Windows PowerShell Startup Script
# Handles UTF-8 encoding for proper emoji display

Write-Host "Starting Discord Clan Storage Bot..." -ForegroundColor Green
Write-Host ""

# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# Set environment variables for Python UTF-8 support
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSFSENCODING = "utf-8"

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Install/update requirements if needed
if (Test-Path "requirements.txt") {
    Write-Host "Checking dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "Please edit .env file with your configuration before running again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    } else {
        Write-Host "Error: Neither .env nor .env.example found." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if Google credentials exist
if (-not (Test-Path "credentials\google_service_account.json")) {
    Write-Host "Warning: Google credentials not found at credentials\google_service_account.json" -ForegroundColor Yellow
    Write-Host "Please place your Google service account JSON file there." -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway"
}

# Create necessary directories
@("logs", "data", "credentials") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
        Write-Host "Created directory: $_" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Starting bot with UTF-8 encoding support..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Cyan
Write-Host ""

# Run the bot
try {
    python main.py
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "Bot exited normally." -ForegroundColor Green
    } else {
        Write-Host "Bot exited with error code: $exitCode" -ForegroundColor Red
    }
} catch {
    Write-Host "Error running bot: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"