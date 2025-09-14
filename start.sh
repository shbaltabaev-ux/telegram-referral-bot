#!/bin/bash
set -e

# Check if virtual environment exists, if not create it
if [ ! -d "/app/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /app/venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source /app/venv/bin/activate

# Install dependencies if needed
echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

# Start the bot
echo "Starting bot..."
/app/venv/bin/python bot.py
