"""
Smooth Wave Hub75 - Optimized HUB75 Animation
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
{}
}

def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Smooth Wave Hub75 animation frame renderer.
    
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
    
    """
        Ultra-smooth wave animation with minimal computation
        """
        width = config.hub75.cols
        height = config.hub75.rows
        total_pixels = width * height
    
        # Very slow time progression for smoothness
        t1 = frame * 0.01
        t2 = frame * 0.007
    
        # Pre-calculate constants
        w_factor = 3.14159 / width
        h_factor = 3.14159 / height
    
        for i in range(total_pixels):
            x = i % width
            y = i // width
        
            # Simple sine wave combination - no complex math
            v1 = math.sin(x * w_factor + t1)
            v2 = math.sin(y * h_factor + t2)
        
            # Combine waves
            value = (v1 + v2 + 2) * 0.25  # Normalize to 0-1
        
            # Simple color calculation
            hue = value * 360
        
            # Direct color mapping - no complex HSV conversion
            if hue < 60:
                r = 255
                g = int(hue * 4.25)
                b = 0
            elif hue < 120:
                r = int((120 - hue) * 4.25)
                g = 255
                b = 0
            elif hue < 180:
                r = 0
                g = 255
                b = int((hue - 120) * 4.25)
            elif hue < 240:
                r = 0
                g = int((240 - hue) * 4.25)
                b = 255
            elif hue < 300:
                r = int((hue - 240) * 4.25)
                g = 0
                b = 255
            else:
                r = 255
                g = 0
                b = int((360 - hue) * 4.25)
        
            # Apply brightness with bit shifting for speed
            brightness = int(config.brightness * 255)
            r = (r * brightness) >> 8
            g = (g * brightness) >> 8
            b = (b * brightness) >> 8
        
            pixels[i] = (r, g, b)

    # Animation metadata
    ANIMATION_INFO = {
        'name': 'Smooth Wave',
        'description': 'Ultra-smooth wave pattern optimized for HUB75',
        'author': 'LightBox',
        'version': '1.0'
    }

# Animation metadata
ANIMATION_INFO = {
    "name": "Smooth Wave Hub75",
    "description": "HUB75 LED Matrix Animation",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect'],
    "fps_target": 30
}
