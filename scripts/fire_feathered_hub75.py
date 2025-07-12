"""
Feathered Fire Animation for HUB75
Realistic fire effect with smooth feathering and enhanced realism
"""

import random
import math

# Pre-generate heat map with extra border for feathering
heat_map = [[0.0 for _ in range(66)] for _ in range(66)]

def animate(pixels, config, frame):
    """
    Fire effect with smooth feathering
    """
    width = config.matrix_width
    height = config.matrix_height
    total_pixels = width * height
    
    # Add some time-based variation
    time = frame * 0.1
    
    # Update heat map with more sophisticated fire simulation
    if frame % 2 == 0:  # Update every other frame
        # Add random heat sources at bottom with variation
        for x in range(1, width + 1):
            # Create hot spots that move slightly
            base_heat = random.random() * 0.7 + 0.3
            # Add periodic hot spots that move across the bottom
            hot_spot = math.sin(x * 0.2 + time) * 0.3 + 0.7
            heat_map[height][x] = base_heat * hot_spot
        
        # Propagate heat upward with feathering
        for y in range(height - 1, 0, -1):
            for x in range(1, width + 1):
                # Gather heat from below with wider sampling for smoother flow
                heat = 0
                total_weight = 0
                
                # Sample from 5 pixels below for feathering
                for dx in range(-2, 3):
                    if 0 <= x + dx <= width + 1:
                        # Gaussian-like weights for smooth blending
                        weight = math.exp(-(dx * dx) / 2.0)
                        heat += heat_map[y + 1][x + dx] * weight
                        total_weight += weight
                
                heat /= total_weight
                
                # Add turbulence for more realistic fire movement
                turbulence = (random.random() - 0.5) * 0.1
                heat += turbulence
                
                # Cool as it rises, with variable cooling based on position
                cooling = 0.55 - (y / height) * 0.1  # Less cooling at bottom
                heat_map[y][x] = max(0, heat * cooling)
                
                # Add occasional embers that rise higher
                if random.random() < 0.001:
                    heat_map[y][x] = min(1.0, heat_map[y][x] + 0.5)
    
    # Render fire with smooth gradients
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Sample heat with bilinear interpolation for ultra-smooth rendering
        heat = 0
        sample_count = 0
        
        # Sample surrounding pixels for feathering
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                sx = x + dx + 1  # Offset for border
                sy = y + dy + 1
                
                if 0 <= sx <= width + 1 and 0 <= sy <= height + 1:
                    # Distance-based weight for sampling
                    dist = math.sqrt(dx*dx + dy*dy)
                    weight = 1.0 / (1.0 + dist)
                    heat += heat_map[sy][sx] * weight
                    sample_count += weight
        
        heat /= sample_count
        
        # Add subtle noise for texture
        noise = (random.random() - 0.5) * 0.02
        heat += noise
        heat = max(0, min(1, heat))
        
        # Enhanced color mapping with more transitions
        if heat > 0.95:
            # Blue-white core (hottest)
            r = 240 + int(15 * (heat - 0.95) / 0.05)
            g = 240 + int(15 * (heat - 0.95) / 0.05)
            b = 255
        elif heat > 0.85:
            # White hot
            intensity = (heat - 0.85) / 0.1
            r = 255
            g = 255
            b = 240 + int(15 * intensity)
        elif heat > 0.7:
            # Yellow-white
            intensity = (heat - 0.7) / 0.15
            r = 255
            g = 255
            b = int(200 * (1 - intensity))
        elif heat > 0.5:
            # Yellow to orange
            intensity = (heat - 0.5) / 0.2
            r = 255
            g = 200 + int(55 * intensity)
            b = int(50 * (1 - intensity))
        elif heat > 0.3:
            # Orange to red
            intensity = (heat - 0.3) / 0.2
            r = 255
            g = int(180 * intensity)
            b = 0
        elif heat > 0.15:
            # Dark red with glow
            intensity = (heat - 0.15) / 0.15
            r = 100 + int(155 * intensity)
            g = int(30 * intensity)
            b = 0
        elif heat > 0.05:
            # Very dark red/ember
            intensity = heat / 0.15
            r = int(100 * intensity)
            g = 0
            b = 0
        else:
            # Black with possible faint glow
            r = int(20 * heat / 0.05)
            g = 0
            b = 0
        
        # Apply edge feathering for smooth boundaries
        edge_distance = min(x, width - 1 - x, height - 1 - y)
        if edge_distance < 3:
            edge_fade = edge_distance / 3.0
            r = int(r * edge_fade)
            g = int(g * edge_fade)
            b = int(b * edge_fade)
        
        # Apply brightness and gamma correction for more realistic glow
        gamma = 1.8
        r = int(pow(r / 255.0, 1.0 / gamma) * 255 * config.brightness)
        g = int(pow(g / 255.0, 1.0 / gamma) * 255 * config.brightness)
        b = int(pow(b / 255.0, 1.0 / gamma) * 255 * config.brightness)
        
        # Ensure valid range
        pixels[i] = (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b))
        )

# Animation metadata
ANIMATION_INFO = {
    'name': 'Feathered Fire',
    'description': 'Realistic fire with smooth feathering and enhanced color transitions',
    'author': 'LightBox',
    'version': '2.0',
    'features': [
        'Smooth feathering with multi-pixel sampling',
        'Realistic turbulence and flow',
        'Enhanced color gradients with blue-white core',
        'Moving hot spots at the base',
        'Occasional rising embers',
        'Edge feathering for smooth boundaries',
        'Gamma correction for realistic glow'
    ]
}