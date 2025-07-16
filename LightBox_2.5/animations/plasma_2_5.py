"""
Plasma Hub75 - Optimized HUB75 Animation
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
    "hue_offset": 0.3,
    "gamma": 2.2,
}


def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Plasma Hub75 animation frame renderer.
    
    Args:
        pixels: List of RGB pixel values to modify in-place
        config: Configuration object with parameters
        frame: Current frame number
    """
    # Get matrix dimensions
    width = config.get("hub75.cols", 64)
    height = config.get("hub75.rows", 64)
    
    # Get animation parameters with defaults
    speed = config.get("animations.speed", config.get("speed", 1.0))
    brightness = config.get("brightness", 1.0) 
    intensity = config.get("animations.intensity", DEFAULT_PARAMS["intensity"])
    scale = config.get("animations.scale", DEFAULT_PARAMS["scale"])
    hue_shift = config.get("animations.hue_shift", DEFAULT_PARAMS["hue_shift"])
    saturation = config.get("animations.saturation", DEFAULT_PARAMS["saturation"])
    color_intensity = config.get("animations.color_intensity", 
                                DEFAULT_PARAMS["color_intensity"])
    
    # Time-based animation using frame count
    t = frame * config.get("animations.time_scale", 0.05) * speed
    
    # Plasma animation - Multi-layered sine wave interference
    for y in range(height):
        for x in range(width):
            # Calculate index directly
            idx = y * width + x
            
            # Create plasma effect using multiple sine waves
            # Normalize coordinates to [-1, 1] range
            nx = (x - width / 2) / (width / 2)
            ny = (y - height / 2) / (height / 2)
            
            # Multiple sine wave layers for complex plasma pattern
            wave1 = math.sin(nx * 5 * scale + t * 2.0)
            wave2 = math.sin(ny * 4 * scale + t * 1.5)
            wave3 = math.sin((nx + ny) * 3 * scale + t * 1.8)
            wave4 = math.sin(math.sqrt(nx*nx + ny*ny) * 6 * scale + t * 2.5)
            
            # Combine waves for plasma effect
            plasma = (wave1 + wave2 + wave3 + wave4) / 4.0
            plasma_intensity = (plasma + 1.0) / 2.0 * intensity
            
            # Create color cycling effect
            hue_base = config.get("animations.hue_offset", 0.3)
            hue = (hue_base + plasma_intensity * 0.8 + t * 0.1 + hue_shift) % 1.0
            sat = saturation
            value = brightness * plasma_intensity * color_intensity
            
            # Convert HSV to RGB
            r, g, b = config.hsv_to_rgb(hue, sat, value)
            
            # Apply gamma correction
            gamma = config.get("animations.gamma", 2.2)
            r = config.gamma_correct(r, gamma)
            g = config.gamma_correct(g, gamma)
            b = config.gamma_correct(b, gamma)
            
            if 0 <= idx < len(pixels):
                pixels[idx] = (int(r * 255), int(g * 255), int(b * 255))


# Animation metadata
ANIMATION_INFO = {
    "name": "Plasma Hub75",
    "description": "Multi-layered sine wave plasma effect for HUB75 LED Matrix",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect', 'plasma'],
    "fps_target": 30
}
