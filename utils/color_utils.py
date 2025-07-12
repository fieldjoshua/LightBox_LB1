"""
Color utility functions for LightBox.
Provides optimized color space conversions and manipulations.
"""

import colorsys
from typing import Tuple, List, Dict
from functools import lru_cache


@lru_cache(maxsize=256)
def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """
    Convert HSV color to RGB with caching.
    
    Args:
        h: Hue (0.0-1.0)
        s: Saturation (0.0-1.0)
        v: Value/brightness (0.0-1.0)
        
    Returns:
        Tuple of (r, g, b) with values 0-255
    """
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert RGB color to HSV.
    
    Args:
        r: Red (0-255)
        g: Green (0-255)
        b: Blue (0-255)
        
    Returns:
        Tuple of (h, s, v) with values 0.0-1.0
    """
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)


def blend_colors(color1: Tuple[int, int, int], 
                 color2: Tuple[int, int, int], 
                 factor: float) -> Tuple[int, int, int]:
    """
    Blend two RGB colors together.
    
    Args:
        color1: First RGB color
        color2: Second RGB color
        factor: Blend factor (0.0 = color1, 1.0 = color2)
        
    Returns:
        Blended RGB color
    """
    factor = max(0.0, min(1.0, factor))
    return (
        int(color1[0] * (1 - factor) + color2[0] * factor),
        int(color1[1] * (1 - factor) + color2[1] * factor),
        int(color1[2] * (1 - factor) + color2[2] * factor)
    )


def apply_brightness(color: Tuple[int, int, int], 
                    brightness: float) -> Tuple[int, int, int]:
    """
    Apply brightness scaling to an RGB color.
    
    Args:
        color: RGB color tuple
        brightness: Brightness factor (0.0-1.0)
        
    Returns:
        Brightness-adjusted RGB color
    """
    brightness = max(0.0, min(1.0, brightness))
    return (
        int(color[0] * brightness),
        int(color[1] * brightness),
        int(color[2] * brightness)
    )


def wheel_color(pos: int) -> Tuple[int, int, int]:
    """
    Get a color from the color wheel.
    
    Args:
        pos: Position on wheel (0-255)
        
    Returns:
        RGB color from the wheel position
    """
    pos = pos % 256
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)


def gradient(start_color: Tuple[int, int, int],
             end_color: Tuple[int, int, int],
             steps: int) -> List[Tuple[int, int, int]]:
    """
    Generate a gradient between two colors.
    
    Args:
        start_color: Starting RGB color
        end_color: Ending RGB color
        steps: Number of steps in gradient
        
    Returns:
        List of RGB colors forming the gradient
    """
    if steps <= 1:
        return [start_color]
    
    gradient_colors = []
    for i in range(steps):
        factor = i / (steps - 1)
        gradient_colors.append(blend_colors(start_color, end_color, factor))
    
    return gradient_colors


def interpolate_palette(colors: List[Tuple[int, int, int]], 
                       size: int) -> List[Tuple[int, int, int]]:
    """
    Interpolate a color palette to a specific size.
    
    Args:
        colors: List of RGB colors
        size: Desired palette size
        
    Returns:
        Interpolated palette of the specified size
    """
    if not colors:
        return [(0, 0, 0)] * size
    
    if len(colors) == 1:
        return [colors[0]] * size
    
    if len(colors) >= size:
        # Sample evenly from the palette
        step = len(colors) / size
        return [colors[int(i * step)] for i in range(size)]
    
    # Interpolate between colors
    result = []
    segment_size = size // (len(colors) - 1)
    remainder = size % (len(colors) - 1)
    
    for i in range(len(colors) - 1):
        segment_steps = segment_size + (1 if i < remainder else 0)
        segment = gradient(colors[i], colors[i + 1], segment_steps + 1)
        result.extend(segment[:-1])  # Exclude last to avoid duplicates
    
    result.append(colors[-1])  # Add final color
    
    return result[:size]  # Ensure exact size


def clamp_rgb(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """
    Clamp RGB values to valid range (0-255).
    
    Args:
        r: Red value
        g: Green value
        b: Blue value
        
    Returns:
        Clamped RGB tuple
    """
    return (
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b)))
    )


# Common color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)