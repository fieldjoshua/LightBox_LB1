#!/usr/bin/env python3
"""
Matrix Configuration Test - Find the correct settings for full 64x64 display
"""

import signal
import sys
import time

# Test different configurations for 64x64 matrix
CONFIGS = [
    # Standard single 64x64 panel
    {"rows": 64, "cols": 64, "chain_length": 1, "parallel": 1, "hardware_mapping": "adafruit-hat"},
    {"rows": 64, "cols": 64, "chain_length": 1, "parallel": 1, "hardware_mapping": "adafruit-hat-pwm"},

    # Two 32x64 panels chained horizontally
    {"rows": 64, "cols": 32, "chain_length": 2, "parallel": 1, "hardware_mapping": "adafruit-hat"},
    {"rows": 64, "cols": 32, "chain_length": 2, "parallel": 1, "hardware_mapping": "adafruit-hat-pwm"},

    # Two 64x32 panels stacked vertically
    {"rows": 32, "cols": 64, "chain_length": 1, "parallel": 2, "hardware_mapping": "adafruit-hat"},
    {"rows": 32, "cols": 64, "chain_length": 1, "parallel": 2, "hardware_mapping": "adafruit-hat-pwm"},

    # Alternative hardware mappings
    {"rows": 64, "cols": 64, "chain_length": 1, "parallel": 1, "hardware_mapping": "regular"},
    {"rows": 64, "cols": 64, "chain_length": 1, "parallel": 1, "hardware_mapping": "adafruit-hat-pwm-slow"},
]

def signal_handler(sig, frame):
    print("\n🛑 Test interrupted")
    sys.exit(0)

def test_config(config, test_num):
    print(f"\n🧪 Test {test_num}: {config}")

    try:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

        # Configure matrix
        options = RGBMatrixOptions()
        options.rows = config["rows"]
        options.cols = config["cols"]
        options.chain_length = config["chain_length"]
        options.parallel = config["parallel"]
        options.hardware_mapping = config["hardware_mapping"]
        options.gpio_slowdown = 2
        options.brightness = 80
        options.pwm_bits = 8
        options.pwm_lsb_nanoseconds = 100
        options.pwm_dither_bits = 2
        options.limit_refresh_rate_hz = 120

        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        # Test pattern: Fill screen with different colors in quadrants
        width = canvas.width
        height = canvas.height

        print(f"   📐 Canvas size: {width}x{height}")

        # Fill quadrants with different colors
        for y in range(height):
            for x in range(width):
                if x < width//2 and y < height//2:
                    canvas.SetPixel(x, y, 255, 0, 0)  # Red top-left
                elif x >= width//2 and y < height//2:
                    canvas.SetPixel(x, y, 0, 255, 0)  # Green top-right
                elif x < width//2 and y >= height//2:
                    canvas.SetPixel(x, y, 0, 0, 255)  # Blue bottom-left
                else:
                    canvas.SetPixel(x, y, 255, 255, 0)  # Yellow bottom-right

        canvas = matrix.SwapOnVSync(canvas)

        print("   ✅ Matrix initialized successfully!")
        print("   🎨 Test pattern displayed for 5 seconds")
        print("   📝 Expected: 4 colored quadrants filling entire 64x64 screen")
        print("   ❓ Do you see the FULL 64x64 screen filled? (y/n): ", end="", flush=True)

        # Wait for test
        time.sleep(5)

        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("🌈 Matrix Configuration Test")
    print("=" * 50)
    print("This will test different configurations to find your working setup.")
    print("Watch your LED matrix during each test!")
    print("=" * 50)

    for i, config in enumerate(CONFIGS, 1):
        if test_config(config, i):
            print("\n⏳ Displaying test pattern for 10 seconds...")
            print("🔍 Check if the ENTIRE 64x64 matrix is filled with 4 colored quadrants")
            time.sleep(10)

            response = input("\n✅ Did this configuration show the FULL screen? (y/n): ").lower().strip()
            if response == 'y':
                print("\n🎉 FOUND WORKING CONFIGURATION!")
                print(f"📋 Config: {config}")
                print("\n🔧 Use these settings in LBQualm:")
                for key, value in config.items():
                    print(f"   {key}: {value}")
                return config
            else:
                print(f"❌ Configuration {i} rejected")

        print("⏭️  Moving to next configuration...")
        time.sleep(2)

    print("\n😞 No working configuration found in standard tests")
    print("📝 Your matrix may need custom settings")
    return None

if __name__ == "__main__":
    result = main()
    if result:
        print("\n🏁 Test completed successfully!")
    else:
        print("\n🔧 Manual configuration may be needed")
