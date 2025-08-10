import math

# Optional metadata
PARAMS = {
    "speed": 1.0
}

def animate(pixels, config, frame):
    """Minimal aurora-like animation."""
    width = int(config.get("hub75.cols", 64) or 64)
    height = int(config.get("hub75.rows", 64) or 64)
    speed = float(config.get("animations.speed", PARAMS["speed"]) or 1.0)

    f = frame * 0.05 * speed
    for y in range(height):
        for x in range(width):
            # Three soft waves offset in phase
            r = int(255 * (0.5 + 0.5 * math.sin((x*0.10) + f)))
            g = int(255 * (0.5 + 0.5 * math.sin((y*0.12) + f + 2.1)))
            b = int(255 * (0.5 + 0.5 * math.sin(((x+y)*0.08) + f + 4.2)))
            idx = y * width + x
            if 0 <= idx < len(pixels):
                pixels[idx] = (r//2, g, b//2)
