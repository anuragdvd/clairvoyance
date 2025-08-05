#!/bin/bash

# Setup script for Simple Voice Agent
echo "Setting up Simple Voice Agent..."

# Create virtual environment if it doesn't exist
if [ ! -d "application/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv application/venv
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source application/venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. source application/venv/bin/activate"
echo "2. python run.py"
echo ""
echo "Make sure to set up your .env file with the required API keys first!"