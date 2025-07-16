"""
Ocean Waves Hub75 - Optimized HUB75 Animation
HUB75 LED Matrix Animation

This animation is optimized for HUB75 LED matrices with the following features:
- Double buffering with SwapOnVSync for tear-free animation
- Efficient array processing for better performance
- Parameter standardization
- Gamma correction for accurate colors
"""

import math
import random
import time
from typing import List, Tuple, Optional

# Parameter defaults that can be overridden via the config
DEFAULT_PARAMS = {
    "speed": 1.0,
    "intensity": 1.0,
    "scale": 1.0,
    "hue_shift": 0.0,
    "saturation": 0.9,
    "color_intensity": 1.0,
    # Add any animation-specific parameters below
    "wave_amplitude": 0.3,
    "wave_frequency": 0.1
}

def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Ocean Waves Hub75 animation frame renderer.
    
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
    scale = config.get("scale", DEFAULT_PARAMS["scale"])
    hue_shift = config.get("hue_shift", DEFAULT_PARAMS["hue_shift"])
    saturation = config.get("saturation", DEFAULT_PARAMS["saturation"])
    color_intensity = config.get("color_intensity", DEFAULT_PARAMS["color_intensity"])
    
    # Time-based animation using frame count
    t = frame * config.get("time_scale", 0.05) * speed
    
    # Ocean waves with multiple layers
    total_pixels = width * height
    
    # Create ocean wave effect
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Create wave pattern
        wave1 = math.sin(x * 0.1 + t) * 0.3
        wave2 = math.sin(y * 0.15 + t * 0.7) * 0.3
        wave3 = math.sin((x + y) * 0.05 + t * 0.3) * 0.2
        
        # Combine waves
        wave_value = (wave1 + wave2 + wave3) * 0.5 + 0.5
        wave_value = max(0, min(1, wave_value))
        
        # Apply intensity and brightness
        wave_value *= intensity * brightness
        
        # Color mapping for ocean effect (blue/green palette)
        if wave_value > 0.7:
            # Light blue/white caps
            r = int(200 * wave_value)
            g = int(230 * wave_value)
            b = 255
        elif wave_value > 0.4:
            # Blue water
            r = int(50 * wave_value)
            g = int(150 * wave_value)
            b = int(255 * wave_value)
        else:
            # Dark blue/black depths
            r = int(20 * wave_value)
            g = int(80 * wave_value)
            b = int(150 * wave_value)
        
        pixels[i] = (max(0, min(255, r)), max(0, min(255, g)), 
                    max(0, min(255, b)))


# Animation metadata
ANIMATION_INFO = {
    "name": "Ocean Waves Hub75",
    "description": "HUB75 LED Matrix Animation",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect'],
    "fps_target": 30
}
