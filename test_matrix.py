#!/usr/bin/env python3
"""
Simple test script for HUB75 LED matrix
"""

import time
import sys
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'
options.gpio_slowdown = 2
options.brightness = 50
options.disable_hardware_pulsing = True  # Add this to avoid sound module conflict

# Create the matrix
matrix = RGBMatrix(options=options)

try:
    print("Press CTRL-C to stop")
    
    # Fill the matrix with red
    for x in range(options.cols):
        for y in range(options.rows):
            matrix.SetPixel(x, y, 255, 0, 0)
    
    time.sleep(2)
    
    # Fill the matrix with green
    for x in range(options.cols):
        for y in range(options.rows):
            matrix.SetPixel(x, y, 0, 255, 0)
    
    time.sleep(2)
    
    # Fill the matrix with blue
    for x in range(options.cols):
        for y in range(options.rows):
            matrix.SetPixel(x, y, 0, 0, 255)
    
    time.sleep(2)
    
    # Clear the matrix
    matrix.Clear()
    
except KeyboardInterrupt:
    print("Exiting...")
    matrix.Clear()
    sys.exit(0) 