#!/usr/bin/env python3
"""Simple test script to verify HUB75 matrix lights are working."""

import sys
import time
from pathlib import Path

from core.config import ConfigManager
from core.conductor import Conductor

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))


def simple_test_animation(pixels, config, frame):
    """Simple rainbow animation to test if lights work."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    # Create a simple rainbow wave pattern
    for y in range(height):
        for x in range(width):
            # Calculate color based on position and time
            hue = (x + y + frame * 0.1) % 360
            
            # Convert HSV to RGB
            h = hue / 60.0
            c = 1.0
            x_val = c * (1 - abs((h % 2) - 1))
            
            if h < 1:
                r, g, b = c, x_val, 0
            elif h < 2:
                r, g, b = x_val, c, 0
            elif h < 3:
                r, g, b = 0, c, x_val
            elif h < 4:
                r, g, b = 0, x_val, c
            elif h < 5:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val
            
            # Convert to 0-255 range
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            
            # Set pixel
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def main():
    """Test the HUB75 matrix directly."""
    print("🌈 Testing HUB75 Matrix Lights")
    print("=" * 40)
    
    # Initialize configuration
    try:
        config = ConfigManager("config/settings.json")
        print(f"✅ Configuration loaded - Platform: {config.platform}")
        print(f"   Matrix: {config.get('hub75.cols')}x"
              f"{config.get('hub75.rows')}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False
    
    # Initialize conductor
    try:
        conductor = Conductor(config)
        print("✅ Conductor created")
        
        # Initialize hardware
        if conductor.initialize():
            print("✅ Hardware initialized")
        else:
            print("⚠️  Hardware initialization issues")
    except Exception as e:
        print(f"❌ Conductor initialization failed: {e}")
        return False
    
    # Test matrix directly
    if not conductor.matrix:
        print("❌ Matrix not available")
        return False
    
    print(f"✅ Matrix ready: {conductor.matrix.num_pixels} pixels")
    print("🎨 Starting rainbow test animation...")
    print("   Press Ctrl+C to stop")
    
    # Create pixel buffer
    pixels = [(0, 0, 0)] * conductor.matrix.num_pixels
    
    try:
        frame = 0
        while True:
            # Run test animation
            simple_test_animation(pixels, config, frame)
            
            # Update matrix
            conductor.matrix.update(pixels)
            
            # Small delay
            time.sleep(0.05)  # 20 FPS
            frame += 1
            
            # Print status every 100 frames
            if frame % 100 == 0:
                print(f"Frame {frame} - Lights should be visible!")
                
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        
        # Clear the matrix
        clear_pixels = [(0, 0, 0)] * conductor.matrix.num_pixels
        conductor.matrix.update(clear_pixels)
        print("✅ Matrix cleared")
    
    return True


if __name__ == "__main__":
    try:
        if main():
            print("✅ Light test completed")
        else:
            print("❌ Light test failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1) 