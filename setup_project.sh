#!/bin/bash

echo "🛡️ Setting up Crypto Guard Project..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p live_trading_results
mkdir -p scalper_results
mkdir -p ultra_scalp_results
mkdir -p models

echo "✅ Setup complete! To start the dashboard, run: make dashboard"
echo "To start the ultra-scalper, run: make scalp"
