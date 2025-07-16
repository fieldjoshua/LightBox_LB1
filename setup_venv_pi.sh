#!/bin/bash

echo "Setting up virtual environment for LightBox2.0 on Raspberry Pi..."

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

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Install the rpi-rgb-led-matrix library if it exists
if [ -d "rpi-rgb-led-matrix" ]; then
    echo "Installing rpi-rgb-led-matrix library..."
    cd rpi-rgb-led-matrix
    make
    cd bindings/python
    pip install -e .
    cd ../../..
else
    echo "Warning: rpi-rgb-led-matrix directory not found. HUB75 matrix support will not be available."
    echo "Please clone the repository from https://github.com/hzeller/rpi-rgb-led-matrix"
fi

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate" 