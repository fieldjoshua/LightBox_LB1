"""
Color utility functions for LightBox.
"""

from typing import Tuple


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """Convert HSV color to RGB.
    
    Args:
        h: Hue (0.0 to 1.0)
        s: Saturation (0.0 to 1.0)
        v: Value (0.0 to 1.0)
        
    Returns:
        Tuple of (r, g, b) values (0-255)
    """
    if s == 0.0:
        return int(v * 255), int(v * 255), int(v * 255)
    
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    
    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB color to HSV.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        
    Returns:
        Tuple of (h, s, v) values (0.0-1.0)
    """
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val
    
    # Value
    v = max_val
    
    # Saturation
    if max_val == 0:
        s = 0
    else:
        s = delta / max_val
    
    # Hue
    if delta == 0:
        h = 0  # Achromatic (gray)
    else:
        if max_val == r:
            h = ((g - b) / delta) % 6
        elif max_val == g:
            h = (b - r) / delta + 2
        else:  # max_val == b
            h = (r - g) / delta + 4
        
        h /= 6
    
    return h, s, v


def gamma_correct(r: int, g: int, b: int, gamma: float = 2.2) -> Tuple[int, int, int]:
    """Apply gamma correction to RGB values.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        gamma: Gamma value (typically 2.2)
        
    Returns:
        Gamma-corrected RGB tuple
    """
    r = int(pow(r / 255.0, gamma) * 255)
    g = int(pow(g / 255.0, gamma) * 255)
    b = int(pow(b / 255.0, gamma) * 255)
    
    return r, g, b


def blend_colors(color1: Tuple[int, int, int], 
                color2: Tuple[int, int, int], 
                factor: float) -> Tuple[int, int, int]:
    """Blend two colors together.
    
    Args:
        color1: First RGB color
        color2: Second RGB color
        factor: Blend factor (0.0 = color1, 1.0 = color2)
        
    Returns:
        Blended RGB color
    """
    factor = max(0.0, min(1.0, factor))
    inv_factor = 1.0 - factor
    
    r = int(color1[0] * inv_factor + color2[0] * factor)
    g = int(color1[1] * inv_factor + color2[1] * factor)
    b = int(color1[2] * inv_factor + color2[2] * factor)
    
    return r, g, b