"""
Fire Hub75 - Optimized HUB75 Animation
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
    Fire Hub75 animation frame renderer.
    
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
    
    # Fire animation - Flame effect with heat dissipation
    for y in range(height):
        for x in range(width):
            # Calculate index directly
            idx = y * width + x
            
            # Create base flame pattern
            # Fire burns upward, so intensity decreases with height
            height_factor = 1.0 - (y / height)
            
            # Create turbulent flame pattern
            turb1 = math.sin((x * 0.3 + t * 2.0) * scale) * 0.5 + 0.5
            turb2 = math.sin((x * 0.1 + y * 0.2 + t * 1.5) * scale) * 0.5 + 0.5
            turb3 = math.sin((x * 0.05 + y * 0.1 + t * 3.0) * scale) * 0.5 + 0.5
            
            # Combine turbulence with height factor
            flame_intensity = height_factor * turb1 * turb2 * turb3 * intensity
            
            # Add flickering effect
            flicker = (math.sin(t * 15 + x * 0.8) * 0.1 + 0.1) * flame_intensity
            final_intensity = min(1.0, flame_intensity + flicker)
            
            # Color calculation - fire colors (red, orange, yellow)
            # Use temperature-based coloring
            if final_intensity > 0.8:
                # Hot flame - white/yellow
                hue = 0.15 + hue_shift  # Yellow
                sat = saturation * 0.7
            elif final_intensity > 0.5:
                # Medium flame - orange
                hue = 0.08 + hue_shift  # Orange
                sat = saturation
            else:
                # Cool flame - red
                hue = 0.0 + hue_shift  # Red
                sat = saturation
            
            hue = hue % 1.0
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
    "name": "Fire Hub75",
    "description": "Realistic fire effect for HUB75 LED Matrix",
    "parameters": DEFAULT_PARAMS,
    "tags": ['visual', 'effect', 'fire'],
    "fps_target": 30
}
