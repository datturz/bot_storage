#!/bin/bash

# Discord Clan Storage Bot - Run Script
# Quick start script for running the bot

set -e

echo "🎮 Discord Clan Storage Bot - Quick Start"
echo "========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Current: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration:"
    echo "   - DISCORD_TOKEN"
    echo "   - GOOGLE_SHEETS_ID (if different)"
    echo "   - AUTHORIZED_USERS"
    echo ""
    echo "💡 Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data credentials

# Check credentials
if [ ! -f "credentials/google_service_account.json" ]; then
    echo "⚠️  Google credentials not found!"
    echo "📖 Please read credentials/README.md for setup instructions"
    echo "🔑 Place your google_service_account.json in credentials/ folder"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests (optional)
if command -v pytest &> /dev/null; then
    echo "🧪 Running tests..."
    pytest tests/ -v || echo "⚠️  Some tests failed, continuing..."
fi

# Start the bot
echo "🚀 Starting bot..."
echo "📊 Logs will be saved to logs/bot.log"
echo "🛑 Press Ctrl+C to stop"
echo ""

python main.py