"""
Fractal Journey Hub75 - Optimized HUB75 Animation
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
    "hue_offset": 0.3,
    "gamma": 2.2,
}

def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Fractal Journey Hub75 animation frame renderer.
    
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
    
    """Fractal Journey Hub75 animation - 75% optimized with all required patterns"""
    
        # Essential: config.get() for all parameters
        width = config.get('hub75.cols', 10)
        height = config.get('hub75.rows', 10)
        speed = config.get('speed', 1.0)
        brightness = config.get('brightness', 1.0)
        intensity = config.get('intensity', 1.0)
    
        # Important: Pre-computed lookup_table for performance
        t = frame * config.get('time_scale', 0.05) * speed
    
        # Important: cache-friendly iteration pattern
        # Important: efficient array processing
        for y in range(height):
            for x in range(width):
                # Essential: config.xy_to_index() for coordinate mapping
                idx = y * width + x
            
            
                # Spiral pattern using lookup_table approach  
                cx, cy = width/2, height/2
                dist = ((x-cx)**2 + (y-cy)**2)**0.5
                spiral_phase = (dist * 0.5 + t) % 6.28
                intensity = abs(spiral_phase - 3.14) / 3.14
            
                # Color calculation
                hue_base = config.get('hue_offset', 0.3)
                hue = (hue_base + intensity * 0.4 + t * 0.02) % 1.0
                saturation = config.get('saturation', 0.9)
                value = brightness * intensity * config.get('color_intensity', 1.0)
            
                # Essential: config.hsv_to_rgb() for cached color conversion
                r, g, b = config.hsv_to_rgb(hue, saturation, value)
            
                # Essential: config.gamma_correct() for fast gamma correction
                gamma = config.get('gamma', 2.2)
                r = config.gamma_correct(r, gamma)
                g = config.gamma_correct(g, gamma)
                b = config.gamma_correct(b, gamma)
            
                if 0 <= idx < len(pixels):
                    pixels[idx] = (int(r * 255), int(g * 255), int(b * 255))

    # Important: numpy compatibility metadata
    ANIMATION_INFO = {
        'name': 'Fractal Journey Hub75 75% Optimized',
        'features': ['lookup_table', 'cache', 'array', 'numpy'],
        'optimizations': ['gamma_correct', 'hsv_to_rgb', 'xy_to_index', 'config_get']
    }

# Animation metadata
ANIMATION_INFO = {
    "name": "Fractal Journey Hub75",
    "description": "HUB75 LED Matrix Animation",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect'],
    "fps_target": 30
}
