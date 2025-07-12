"""
Smooth Wave Animation for HUB75
Optimized for minimal computation and smooth rendering
Uses simple math for best performance
"""

import math

def animate(pixels, config, frame):
    """
    Ultra-smooth wave animation with minimal computation
    """
    width = config.matrix_width
    height = config.matrix_height
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