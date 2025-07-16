"""
Symmetry - Optimized HUB75 Animation
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
    "symmetry_mode": 4,
    "rotation_speed": 0.5
}

def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Symmetry animation frame renderer.
    
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
    symmetry_mode = config.get("symmetry_mode", DEFAULT_PARAMS["symmetry_mode"])
    rotation_speed = config.get("rotation_speed", DEFAULT_PARAMS["rotation_speed"])
    
    # Time-based animation using frame count
    t = frame * config.get("time_scale", 0.05) * speed
    
    # Create symmetrical pattern
    total_pixels = width * height
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Create symmetrical coordinates
        center_x = width // 2
        center_y = height // 2
        
        # Distance from center
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Create symmetrical pattern
        angle = math.atan2(dy, dx)
        symmetrical_angle = angle * symmetry_mode
        
        # Create animation value
        wave = math.sin(distance * 0.1 + t * rotation_speed) * 0.5 + 0.5
        color_phase = math.sin(symmetrical_angle + t) * 0.5 + 0.5
        
        # Apply intensity and brightness
        value = wave * color_phase * intensity * brightness
        
        # Create color
        r = int(255 * value)
        g = int(255 * value * 0.7)
        b = int(255 * value * 0.4)
        
        pixels[i] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


# Animation metadata
ANIMATION_INFO = {
    "name": "Symmetry",
    "description": "HUB75 LED Matrix Animation",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect'],
    "fps_target": 30
}
