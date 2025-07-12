"""
Ocean Waves Animation for HUB75
Smooth ocean wave patterns with foam effects
"""

import math

def animate(pixels, config, frame):
    """
    Ocean waves with multiple layers
    """
    width = config.matrix_width
    height = config.matrix_height
    total_pixels = width * height
    
    # Slow time for smooth motion
    time = frame * 0.02 * config.speed
    
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Create multiple wave layers
        # Primary wave
        wave1 = math.sin(x * 0.1 + time) * math.cos(y * 0.05 + time * 0.7)
        
        # Secondary wave at angle
        wave2 = math.sin((x + y) * 0.07 + time * 1.3) * 0.7
        
        # Smaller ripples
        ripple = math.sin(x * 0.3 + y * 0.2 + time * 2) * 0.3
        
        # Combine waves
        wave_height = (wave1 + wave2 + ripple) / 3
        
        # Create depth effect - darker at bottom
        depth = 1.0 - (y / height) * 0.5
        
        # Foam on wave peaks
        foam = max(0, wave_height - 0.5) * 2
        
        # Ocean colors
        if foam > 0.3:
            # White foam
            r = g = b = 0.9 + foam * 0.1
        else:
            # Ocean blue-green
            base_hue = 180 + wave_height * 20  # Cyan to blue
            brightness = 0.3 + abs(wave_height) * 0.4
            
            # Simple HSV for ocean colors
            if base_hue < 195:
                # Cyan-ish
                r = 0
                g = brightness * 0.8
                b = brightness
            else:
                # Deeper blue
                r = 0
                g = brightness * 0.4
                b = brightness
        
        # Apply depth
        r *= depth
        g *= depth
        b *= depth
        
        # Convert to 0-255 and apply brightness
        pixels[i] = (
            int(r * 255 * config.brightness),
            int(g * 255 * config.brightness),
            int(b * 255 * config.brightness)
        )

# Animation metadata
ANIMATION_INFO = {
    'name': 'Ocean Waves',
    'description': 'Peaceful ocean wave simulation',
    'author': 'LightBox',
    'version': '1.0'
}