#!/usr/bin/env python3
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions

configs = [
    {"name": "Config 1: 64x64 adafruit-hat", "rows": 64, "cols": 64, "chain": 1, "parallel": 1, "hw": "adafruit-hat"},
    {"name": "Config 2: 64x64 regular", "rows": 64, "cols": 64, "chain": 1, "parallel": 1, "hw": "regular"},
    {"name": "Config 3: 32x64 chain=2 adafruit-hat", "rows": 32, "cols": 64, "chain": 2, "parallel": 1, "hw": "adafruit-hat"},
    {"name": "Config 4: 32x64 chain=2 regular", "rows": 32, "cols": 64, "chain": 2, "parallel": 1, "hw": "regular"},
]

for i, cfg in enumerate(configs):
    try:
        print(f"\nTesting {cfg['name']}")

        options = RGBMatrixOptions()
        options.rows = cfg["rows"]
        options.cols = cfg["cols"]
        options.chain_length = cfg["chain"]
        options.parallel = cfg["parallel"]
        options.hardware_mapping = cfg["hw"]
        options.gpio_slowdown = 2
        options.brightness = 100

        matrix = RGBMatrix(options=options)
        canvas = matrix.CreateFrameCanvas()

        # Fill with red
        for y in range(canvas.height):
            for x in range(canvas.width):
                canvas.SetPixel(x, y, 255, 0, 0)

        matrix.SwapOnVSync(canvas)
        print(f"Canvas: {canvas.width}x{canvas.height}")
        print("DISPLAYING RED FOR 8 SECONDS - CHECK IF FULL SCREEN!")
        time.sleep(8)

        # Clear screen
        for y in range(canvas.height):
            for x in range(canvas.width):
                canvas.SetPixel(x, y, 0, 0, 0)
        matrix.SwapOnVSync(canvas)
        time.sleep(1)

    except Exception as e:
        print(f"FAILED: {e}")
        continue

print("Test complete!")
