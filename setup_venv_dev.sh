#!/bin/bash

echo "Setting up development virtual environment for LightBox2.0..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install development dependencies
echo "Installing development dependencies from requirements-dev.txt..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate" 