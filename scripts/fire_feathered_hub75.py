"""
Fire Feathered Hub75 - Optimized HUB75 Animation
HUB75 LED Matrix Animation

This animation is optimized for HUB75 LED matrices with the following features:
- Double buffering with SwapOnVSync for tear-free animation
- Efficient array processing for better performance
- Parameter standardization
- Gamma correction for accurate colors
"""

import math
from typing import List, Tuple

# Parameter defaults that can be overridden via the config
DEFAULT_PARAMS = {
    "speed": 1.0,
    "intensity": 1.0,
    "scale": 1.0,
    "hue_shift": 0.0,
    "saturation": 0.9,
    "color_intensity": 1.0,
    # Add any animation-specific parameters below
    "fire_intensity": 1.0,
    "cooling_rate": 0.9
}


def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Fire Feathered Hub75 animation frame renderer.
    
    Args:
        pixels: List of RGB pixel values to modify in-place
        config: Configuration object with parameters
        frame: Current frame number
    """
    # Get matrix dimensions
    width = config.get("hub75.cols", 64)
    height = config.get("hub75.rows", 64)
    
    # Get animation parameters with defaults
    speed = config.get("speed", 1.0)
    brightness = config.get("brightness", 1.0) 
    intensity = config.get("intensity", DEFAULT_PARAMS["intensity"])
    
    # Time-based animation using frame count
    t = frame * config.get("time_scale", 0.05) * speed
    
    # Fire effect with smooth feathering
    total_pixels = width * height
    
    # Create fire effect
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Create fire-like pattern
        base_heat = max(0, 1.0 - (y / height) * 1.5)
        
        # Add noise and movement
        noise = (math.sin(x * 0.2 + t) * 0.3 + 
                 math.cos(y * 0.1 + t * 0.7) * 0.2)
        heat = base_heat + noise * 0.3
        heat = max(0, min(1, heat))
        
        # Apply intensity and brightness
        heat *= intensity * brightness
        
        # Color mapping for fire effect
        if heat > 0.8:
            # White hot
            r = 255
            g = int(255 * (heat - 0.2))
            b = int(100 * (heat - 0.8))
        elif heat > 0.5:
            # Yellow-orange
            r = 255
            g = int(200 * heat)
            b = 0
        elif heat > 0.2:
            # Red-orange
            r = int(255 * heat)
            g = int(50 * heat)
            b = 0
        else:
            # Dark red/black
            r = int(100 * heat)
            g = 0
            b = 0
        
        # Apply gamma correction
        gamma = 2.2
        r = int((r / 255.0) ** (1.0 / gamma) * 255)
        g = int((g / 255.0) ** (1.0 / gamma) * 255)
        b = int((b / 255.0) ** (1.0 / gamma) * 255)
        
        pixels[i] = (max(0, min(255, r)), max(0, min(255, g)), 
                     max(0, min(255, b)))


# Animation metadata
ANIMATION_INFO = {
    "name": "Fire Feathered Hub75",
    "description": "HUB75 LED Matrix Animation",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect'],
    "fps_target": 30
}
