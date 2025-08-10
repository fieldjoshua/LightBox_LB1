#!/usr/bin/env python3
"""
LightBox LED Matrix Controller - Main Entry Point
Optimized implementation with platform-specific enhancements
"""

import sys
import os

# Add the LightBox directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.conductor import main

if __name__ == "__main__":
    sys.exit(main())