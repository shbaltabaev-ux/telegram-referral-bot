#!/bin/bash
set -e

echo "Creating virtual environment..."
python3 -m venv /app/venv

echo "Activating virtual environment..."
source /app/venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"