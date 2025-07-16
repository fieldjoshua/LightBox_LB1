"""
Aurora Hub75 - Optimized HUB75 Animation
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
    "wave_speed": 0.3,
    "color_shift": 0.02
}


def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    Aurora Hub75 animation frame renderer.
    
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
    hue_shift = config.get("animations.hue_shift", 
                          DEFAULT_PARAMS["hue_shift"])
    saturation = config.get("animations.saturation", 
                           DEFAULT_PARAMS["saturation"])
    color_intensity = config.get("animations.color_intensity", 
                                 DEFAULT_PARAMS["color_intensity"])
    
    # Time-based animation using frame count
    t = frame * config.get("animations.time_scale", 0.05) * speed
    
    # Aurora animation - Northern lights effect
    for y in range(height):
        for x in range(width):
            # Calculate index directly
            idx = y * width + x
            
            # Create flowing waves similar to northern lights
            wave1 = math.sin((x * 0.1 + t * 0.5) * scale) * 0.5 + 0.5
            wave2 = math.sin((y * 0.05 + t * 0.3) * scale) * 0.5 + 0.5
            wave3 = math.sin((x * 0.02 + y * 0.03 + t * 0.7) * scale) * 0.5 + 0.5
            
            # Combine waves for aurora effect
            aurora_intensity = (wave1 * wave2 * wave3) * intensity
            
            # Add some randomness for shimmer
            shimmer = (math.sin(t * 10 + x * 0.5 + y * 0.3) * 0.1 + 0.1) * \
                     aurora_intensity
            final_intensity = min(1.0, aurora_intensity + shimmer)
            
            # Color calculation - aurora colors (greens, blues, purples)
            hue_base = config.get("animations.hue_offset", 0.3)  # Start green
            hue = (hue_base + final_intensity * 0.2 + t * 0.02 + 
                   hue_shift) % 1.0
            sat = saturation * (0.8 + final_intensity * 0.2)
            value = brightness * final_intensity * color_intensity
            
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
    "name": "Aurora Hub75",
    "description": "Northern lights effect for HUB75 LED Matrix",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect', 'nature'],
    "fps_target": 30
}
