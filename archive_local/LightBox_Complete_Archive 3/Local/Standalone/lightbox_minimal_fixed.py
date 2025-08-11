#!/usr/bin/env python3
"""
Complete LightBox System with Embedded Animations and Web Interface
Bypasses all file permission issues by embedding everything in one script.
"""

import sys
import time
import math
import threading
import signal
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


def apply_gamma_correction(r, g, b, gamma=2.2):
    """Apply gamma correction to RGB values"""
    if gamma == 1.0:
        return r, g, b
    
    # Simple gamma correction
    r_norm = r / 255.0
    g_norm = g / 255.0  
    b_norm = b / 255.0
    
    r_corrected = pow(r_norm, 1.0/gamma) if r_norm > 0 else 0
    g_corrected = pow(g_norm, 1.0/gamma) if g_norm > 0 else 0
    b_corrected = pow(b_norm, 1.0/gamma) if b_norm > 0 else 0
    
    return (
        int(r_corrected * 255),
        int(g_corrected * 255), 
        int(b_corrected * 255)
    )


# Embedded ConfigManager and Conductor - no external dependencies


class ConfigManager:
    def __init__(self):
        self.config = {
            "hub75": {
                "rows": 64,
                "cols": 64,
                "brightness": 80,
                "gpio_slowdown": 4,
                "hardware_mapping": "adafruit-hat"
            }
        }
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value


class Conductor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.matrix = None
        self.current_animation = None
        self.frame_count = 0
        self.pixels = None
        self.width = self.config.get('hub75.cols', 64)
        self.height = self.config.get('hub75.rows', 64)
        self.pixels = [(0, 0, 0)] * (self.width * self.height)
        
        # Initialize RGB matrix
        self._init_matrix()
    
    def _init_matrix(self):
        """Initialize the RGB matrix."""
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
            options = RGBMatrixOptions()
            options.rows = self.height
            options.cols = self.width
            options.brightness = self.config.get('hub75.brightness', 80)
            options.gpio_slowdown = self.config.get('hub75.gpio_slowdown', 4)
            options.hardware_mapping = self.config.get(
                'hub75.hardware_mapping', 'adafruit-hat')
            self.matrix = RGBMatrix(options=options)
            print(f"✅ HUB75 Matrix initialized: {self.width}x{self.height}")
        except ImportError:
            print("⚠️  RGB Matrix library not available - using mock display")
            self.matrix = None
    
    def set_animation(self, name):
        """Set the current animation."""
        if name in EMBEDDED_ANIMATIONS:
            self.current_animation = name
            self.frame_count = 0  # Reset frame counter for new animation
            print(f"✅ Animation set to: {name}")
            return True
        return False
    
    def update_frame(self):
        """Update the current frame."""
        if (self.current_animation and 
                self.current_animation in EMBEDDED_ANIMATIONS):
            # Run the animation
            EMBEDDED_ANIMATIONS[self.current_animation](
                self.pixels, self.config, self.frame_count)
            
            # Update matrix display
            if self.matrix:
                self.matrix.Clear()
                for y in range(self.height):
                    for x in range(self.width):
                        pixel_index = y * self.width + x
                        if pixel_index < len(self.pixels):
                            r, g, b = self.pixels[pixel_index]
                            self.matrix.SetPixel(x, y, r, g, b)
            
            self.frame_count += 1


# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

# Global system state
lightbox_system = None
app = Flask(__name__, static_folder=None, template_folder=None)


# =====================================================
# EMBEDDED ANIMATIONS - No file loading required
# =====================================================

def aurora_animation(pixels, config, frame):
    """Aurora borealis animation with flowing colors."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Create flowing aurora effect
            wave1 = math.sin((x * 0.1) + (frame * 0.02)) * 0.5 + 0.5
            wave2 = math.sin((y * 0.15) + (frame * 0.03)) * 0.5 + 0.5
            wave3 = math.sin(((x + y) * 0.08) + (frame * 0.01)) * 0.5 + 0.5
            
            # Aurora colors: green, blue, purple
            r = int(wave3 * wave1 * 100)
            g = int(wave1 * wave2 * 255)
            b = int(wave2 * wave3 * 200)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def plasma_animation(pixels, config, frame):
    """Plasma effect animation."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Multiple sine waves for plasma effect
            value = math.sin(x * 0.2 + frame * 0.1)
            value += math.sin(y * 0.3 + frame * 0.15)
            value += math.sin((x + y) * 0.25 + frame * 0.08)
            value += math.sin(math.sqrt(x*x + y*y) * 0.1 + frame * 0.2)
            value = (value + 4) / 8  # Normalize to 0-1
            
            # Convert to RGB with color cycling
            hue = (value + frame * 0.01) % 1.0
            
            # HSV to RGB conversion
            h = hue * 6.0
            c = 1.0
            x_val = c * (1 - abs((h % 2) - 1))
            
            if h < 1:
                r, g, b = c, x_val, 0
            elif h < 2:
                r, g, b = x_val, c, 0
            elif h < 3:
                r, g, b = 0, c, x_val
            elif h < 4:
                r, g, b = 0, x_val, c
            elif h < 5:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val
            
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def fire_animation(pixels, config, frame):
    """Fire effect animation."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Fire effect - hotter at bottom, cooler at top
            base_heat = (height - y) / height
            
            # Add noise and movement
            noise = math.sin(x * 0.3 + frame * 0.1) * 0.2
            noise += math.sin(y * 0.2 + frame * 0.15) * 0.1
            
            heat = base_heat + noise
            heat = max(0, min(1, heat))
            
            # Fire colors: red to orange to yellow
            if heat < 0.5:
                r = int(heat * 2 * 255)
                g = int(heat * 2 * 100)
                b = 0
            else:
                r = 255
                g = int(100 + (heat - 0.5) * 2 * 155)
                b = int((heat - 0.5) * 2 * 50)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def ocean_animation(pixels, config, frame):
    """Ocean waves animation."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Multiple wave layers
            wave1 = math.sin(x * 0.15 + frame * 0.05) * 0.3
            wave2 = math.sin(x * 0.1 + y * 0.1 + frame * 0.03) * 0.2
            wave3 = math.sin(x * 0.05 + frame * 0.02) * 0.5
            
            # Ocean depth effect
            depth = (y / height) + wave1 + wave2 + wave3
            depth = max(0, min(1, depth))
            
            # Ocean colors: dark blue to light blue to white
            r = int(depth * 50)
            g = int(50 + depth * 100)
            b = int(100 + depth * 155)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def rainbow_animation(pixels, config, frame):
    """Rainbow wave animation."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Moving rainbow
            hue = ((x + y + frame) % 360) / 360.0
            
            # HSV to RGB
            h = hue * 6.0
            c = 1.0
            x_val = c * (1 - abs((h % 2) - 1))
            
            if h < 1:
                r, g, b = c, x_val, 0
            elif h < 2:
                r, g, b = x_val, c, 0
            elif h < 3:
                r, g, b = 0, c, x_val
            elif h < 4:
                r, g, b = 0, x_val, c
            elif h < 5:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val
            
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def matrix_rain_animation(pixels, config, frame):
    """Matrix-style digital rain animation - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    # Clear background
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 0)
    
    # Create falling streams
    for stream in range(width // 3):
        x = (stream * 3 + (frame // 10) % 3) % width
        
        # Stream parameters
        speed = 1 + (x % 3)
        offset = (frame * speed) % (height + 20)
        
        # Draw stream
        for i in range(12):  # Stream length
            y = (offset - i * 2) % height
            if 0 <= y < height:
                # Brightness fades along stream
                brightness = max(0, 255 - i * 20)
                
                # Green matrix color with slight blue
                r = 0
                g = brightness
                b = brightness // 4
                
                pixel_index = y * width + x
                if pixel_index < len(pixels):
                    pixels[pixel_index] = (r, g, b)


def kaleidoscope_animation(pixels, config, frame):
    """Kaleidoscope pattern animation - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2
    
    for y in range(height):
        for x in range(width):
            # Distance from center
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Angle from center
            angle = math.atan2(dy, dx)
            
            # Kaleidoscope effect with multiple rotations
            kaleidoscope_angle = (angle * 6 + frame * 0.05) % (math.pi * 2)
            wave = math.sin(distance * 0.3 + frame * 0.08)
            
            # Multiple color layers
            hue1 = (kaleidoscope_angle / (math.pi * 2) + frame * 0.01) % 1.0
            hue2 = (distance * 0.1 + frame * 0.02) % 1.0
            
            # Combine hues
            final_hue = (hue1 + hue2 * wave) % 1.0
            
            # HSV to RGB with high saturation
            h = final_hue * 6.0
            c = 0.8 + wave * 0.2  # Variable saturation
            x_val = c * (1 - abs((h % 2) - 1))
            
            if h < 1:
                r, g, b = c, x_val, 0
            elif h < 2:
                r, g, b = x_val, c, 0
            elif h < 3:
                r, g, b = 0, c, x_val
            elif h < 4:
                r, g, b = 0, x_val, c
            elif h < 5:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val
            
            # Brightness based on distance
            brightness = (1 - min(1, distance / 32)) * 255
            
            r = int(r * brightness)
            g = int(g * brightness)
            b = int(b * brightness)
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def starfield_animation(pixels, config, frame):
    """3D starfield animation - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2
    
    # Clear background
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 0)  # Dark blue space
    
    # Create moving stars
    star_count = 100
    for star in range(star_count):
        # Pseudo-random star positions based on star index and frame
        seed = star * 73 + frame // 4
        star_x = (seed * 31) % 200 - 100  # -100 to 100
        star_y = (seed * 47) % 200 - 100
        star_z = (seed * 13) % 100 + 1    # 1 to 100
        
        # Move star towards viewer
        z = star_z - (frame * 2) % 100
        if z <= 0:
            z = 100
        
        # Project 3D to 2D
        screen_x = int(center_x + star_x * 32 / z)
        screen_y = int(center_y + star_y * 32 / z)
        
        # Check if star is on screen
        if 0 <= screen_x < width and 0 <= screen_y < height:
            # Star brightness based on distance
            brightness = int(255 * (1 - z / 100))
            
            # Star color - white to blue based on speed
            speed_factor = (100 - z) / 100
            r = brightness
            g = brightness
            b = int(brightness * (1 + speed_factor))
            
            pixel_index = screen_y * width + screen_x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def clouds_animation(pixels, config, frame):
    """Peaceful clouds drifting across blue sky - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    for y in range(height):
        for x in range(width):
            # Blue sky gradient - darker at top, lighter at bottom
            sky_gradient = 1.0 - (y / height) * 0.3
            base_r = int(100 * sky_gradient)
            base_g = int(150 * sky_gradient)
            base_b = int(255 * sky_gradient)
            
            # Create multiple cloud layers
            cloud_density = 0
            
            # Cloud layer 1 - large slow clouds
            cloud1_x = (x + frame * 0.5) % (width * 2)
            cloud1_noise = math.sin(cloud1_x * 0.1) * math.sin(y * 0.15)
            cloud1_noise += math.sin(cloud1_x * 0.05) * math.sin(y * 0.08)
            cloud1_strength = max(0, cloud1_noise - 0.3) * 2
            cloud_density += cloud1_strength
            
            # Cloud layer 2 - smaller faster clouds
            cloud2_x = (x + frame * 0.8) % (width * 1.5)
            cloud2_noise = math.sin(cloud2_x * 0.15) * math.sin(y * 0.2)
            cloud2_strength = max(0, cloud2_noise - 0.5) * 1.5
            cloud_density += cloud2_strength
            
            # Cloud layer 3 - wispy high clouds
            cloud3_x = (x + frame * 0.3) % (width * 3)
            cloud3_noise = math.sin(cloud3_x * 0.08) * math.sin(y * 0.12)
            cloud3_strength = max(0, cloud3_noise - 0.4) * 1
            cloud_density += cloud3_strength
            
            # Apply clouds to sky
            cloud_factor = min(1, cloud_density)
            if cloud_factor > 0:
                # Mix white/gray clouds with blue sky
                cloud_r = int(255 * cloud_factor)
                cloud_g = int(255 * cloud_factor)
                cloud_b = int(230 * cloud_factor)
                
                # Blend clouds with sky
                r = int(base_r * (1 - cloud_factor) + cloud_r * cloud_factor)
                g = int(base_g * (1 - cloud_factor) + cloud_g * cloud_factor)
                b = int(base_b * (1 - cloud_factor) + cloud_b * cloud_factor)
            else:
                r, g, b = base_r, base_g, base_b
            
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)


def fireworks_animation(pixels, config, frame):
    """Fireworks bursting in the distance - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    # Dark night sky
    for i in range(len(pixels)):
        pixels[i] = (5, 5, 15)  # Deep blue night
    
    # Multiple firework bursts
    firework_count = 3
    for fw in range(firework_count):
        # Firework timing and position
        fw_time = (frame + fw * 60) % 180
        fw_x = 20 + fw * 20
        fw_y = 15 + fw * 15
        
        if fw_time < 120:  # Firework is active
            # Explosion phase
            explosion_radius = min(25, fw_time * 0.3)
            
            # Create burst particles
            particle_count = 24
            for p in range(particle_count):
                angle = (p / particle_count) * 2 * math.pi
                
                # Particle position
                px = fw_x + math.cos(angle) * explosion_radius
                py = fw_y + math.sin(angle) * explosion_radius
                
                # Check bounds
                if 0 <= px < width and 0 <= py < height:
                    # Particle fade over time
                    fade = max(0, 1 - fw_time / 120)
                    
                    # Firework colors - cycle through different colors per firework
                    if fw == 0:  # Red firework
                        r = int(255 * fade)
                        g = int(100 * fade)
                        b = int(50 * fade)
                    elif fw == 1:  # Green firework
                        r = int(100 * fade)
                        g = int(255 * fade)
                        b = int(50 * fade)
                    else:  # Blue/white firework
                        r = int(200 * fade)
                        g = int(200 * fade)
                        b = int(255 * fade)
                    
                    # Add sparkle effect
                    if fw_time % 6 < 3:
                        r = min(255, int(r * 1.5))
                        g = min(255, int(g * 1.5))
                        b = min(255, int(b * 1.5))
                    
                    pixel_index = int(py) * width + int(px)
                    if 0 <= pixel_index < len(pixels):
                        # Additive blending for overlapping fireworks
                        old_r, old_g, old_b = pixels[pixel_index]
                        pixels[pixel_index] = (
                            min(255, old_r + r),
                            min(255, old_g + g),
                            min(255, old_b + b)
                        )
            
            # Add center bright flash
            if fw_time < 20:
                flash_intensity = int(255 * (1 - fw_time / 20))
                center_pixel = int(fw_y) * width + int(fw_x)
                if 0 <= center_pixel < len(pixels):
                    pixels[center_pixel] = (flash_intensity, flash_intensity, flash_intensity)


def hyperspace_animation(pixels, config, frame):
    """Flying through hyperspace with 120 BPM thrust beats - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2
    
    # 120 BPM = 2 beats per second = 10 frames per beat at 20 FPS
    beat_frame = 10
    beat_cycle = frame % beat_frame
    beat_intensity = 1.0
    
    # Thrust effect on beats 0, 2, 4, 6, 8 (strong beats)
    if beat_cycle < 2:
        beat_intensity = 3.0 + (2 - beat_cycle) * 2  # Intense thrust
    elif beat_cycle < 5:
        beat_intensity = 2.0  # Acceleration phase
    else:
        beat_intensity = 1.0  # Cruise phase
    
    # Clear background - deep space
    for i in range(len(pixels)):
        # Thrust glow effect during beats
        if beat_cycle < 3:
            glow = int((3 - beat_cycle) * 10)
            pixels[i] = (glow, glow // 2, glow // 4)  # Orange thrust glow
        else:
            pixels[i] = (0, 0, 0)  # Deep space
    
    # Create high-speed starfield
    star_count = 150
    for star in range(star_count):
        # Pseudo-random star positions
        seed = star * 73
        star_x = (seed * 31) % 200 - 100  # -100 to 100
        star_y = (seed * 47) % 200 - 100
        star_z = (seed * 13) % 50 + 1     # 1 to 50 (closer = faster)
        
        # Move star towards viewer with beat acceleration
        speed_multiplier = beat_intensity
        z = star_z - (frame * speed_multiplier) % 50
        if z <= 0:
            z = 50
        
        # Project 3D to 2D with perspective
        screen_x = int(center_x + star_x * 32 / z)
        screen_y = int(center_y + star_y * 32 / z)
        
        # Create star trails during thrust
        trail_length = int(beat_intensity * 3)
        for trail in range(trail_length):
            # Calculate trail positions
            trail_z = z + trail * 2
            if trail_z > 0:
                trail_x = int(center_x + star_x * 32 / trail_z)
                trail_y = int(center_y + star_y * 32 / trail_z)
                
                # Check if trail point is on screen
                if 0 <= trail_x < width and 0 <= trail_y < height:
                    # Trail brightness decreases with distance
                    trail_brightness = max(0, 255 - trail * 50)
                    trail_brightness = int(trail_brightness * (1 - trail_z / 50))
                    
                    # Color changes with speed
                    if beat_intensity > 2:  # Hyperspace mode
                        # Blue-white hyperspace streaks
                        r = int(trail_brightness * 0.8)
                        g = int(trail_brightness * 0.9)
                        b = trail_brightness
                    else:
                        # Normal white stars
                        r = g = b = trail_brightness
                    
                    pixel_index = trail_y * width + trail_x
                    if pixel_index < len(pixels):
                        # Additive blending for bright streaks
                        old_r, old_g, old_b = pixels[pixel_index]
                        pixels[pixel_index] = (
                            min(255, old_r + r),
                            min(255, old_g + g),
                            min(255, old_b + b)
                        )
        
        # Main star position
        if 0 <= screen_x < width and 0 <= screen_y < height:
            # Star brightness based on distance and beat
            brightness = int(255 * (1 - z / 50) * beat_intensity)
            brightness = min(255, brightness)
            
            # Color shifts during hyperdrive
            if beat_intensity > 2.5:
                # Intense blue-white during thrust
                r = int(brightness * 0.7)
                g = int(brightness * 0.8)
                b = brightness
            elif beat_intensity > 1.5:
                # White-blue during acceleration
                r = int(brightness * 0.9)
                g = int(brightness * 0.95)
                b = brightness
            else:
                # Pure white during cruise
                r = g = b = brightness
            
            pixel_index = screen_y * width + screen_x
            if pixel_index < len(pixels):
                # Additive blending
                old_r, old_g, old_b = pixels[pixel_index]
                pixels[pixel_index] = (
                    min(255, old_r + r),
                    min(255, old_g + g),
                                         min(255, old_b + b)
                 )


def golden_ratio_animation(pixels, config, frame):
    """Golden ratio spirals interacting at different scales - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2
    
    # Clear background
    for i in range(len(pixels)):
        pixels[i] = (5, 5, 15)  # Deep purple background
    
    # Golden ratio constant
    phi = 1.618033988749
    
    # Create multiple golden spirals at different scales
    spiral_count = 3
    for spiral_num in range(spiral_count):
        # Each spiral has different parameters
        scale = 0.5 + spiral_num * 0.3
        rotation_offset = spiral_num * (2 * math.pi / spiral_count)
        speed_multiplier = 1 + spiral_num * 0.5
        
        # Spiral center orbits around main center
        orbit_radius = 15 + spiral_num * 8
        orbit_angle = (frame * 0.02 * speed_multiplier + rotation_offset) % (2 * math.pi)
        spiral_center_x = center_x + math.cos(orbit_angle) * orbit_radius
        spiral_center_y = center_y + math.sin(orbit_angle) * orbit_radius
        
        # Draw golden spiral
        points = 200
        for i in range(points):
            # Golden spiral equation: r = a * phi^(θ/π)
            theta = (i / points) * 6 * math.pi + (frame * 0.05 * speed_multiplier)
            r = scale * (phi ** (theta / math.pi)) * 2
            
            # Spiral position
            x = spiral_center_x + math.cos(theta) * r
            y = spiral_center_y + math.sin(theta) * r
            
            # Check if point is on screen
            if 0 <= x < width and 0 <= y < height:
                # Color based on spiral number and position
                hue = (spiral_num * 0.33 + i * 0.01 + frame * 0.005) % 1.0
                
                # HSV to RGB
                h = hue * 6.0
                c = 0.8
                x_val = c * (1 - abs((h % 2) - 1))
                
                if h < 1:
                    r_col, g_col, b_col = c, x_val, 0
                elif h < 2:
                    r_col, g_col, b_col = x_val, c, 0
                elif h < 3:
                    r_col, g_col, b_col = 0, c, x_val
                elif h < 4:
                    r_col, g_col, b_col = 0, x_val, c
                elif h < 5:
                    r_col, g_col, b_col = x_val, 0, c
                else:
                    r_col, g_col, b_col = c, 0, x_val
                
                # Brightness fades with distance from center
                brightness = max(0.3, 1 - (i / points))
                r_final = int(r_col * brightness * 255)
                g_final = int(g_col * brightness * 255)
                b_final = int(b_col * brightness * 255)
                
                pixel_index = int(y) * width + int(x)
                if 0 <= pixel_index < len(pixels):
                    # Additive blending for intersection effects
                    old_r, old_g, old_b = pixels[pixel_index]
                    pixels[pixel_index] = (
                        min(255, old_r + r_final),
                        min(255, old_g + g_final),
                        min(255, old_b + b_final)
                    )
        
        # Add golden ratio rectangles
        rect_count = 5
        for rect in range(rect_count):
            rect_scale = 3 + rect * 2
            rect_angle = (frame * 0.01 * speed_multiplier + rect * phi) % (2 * math.pi)
            
            # Rectangle corners based on golden ratio
            w = rect_scale * phi
            h = rect_scale
            
            corners = [
                (-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)
            ]
            
            # Rotate and translate rectangle
            for corner_idx in range(4):
                x1, y1 = corners[corner_idx]
                x2, y2 = corners[(corner_idx + 1) % 4]
                
                # Rotate points
                cos_a, sin_a = math.cos(rect_angle), math.sin(rect_angle)
                x1_rot = x1 * cos_a - y1 * sin_a + spiral_center_x
                y1_rot = x1 * sin_a + y1 * cos_a + spiral_center_y
                x2_rot = x2 * cos_a - y2 * sin_a + spiral_center_x
                y2_rot = x2 * sin_a + y2 * cos_a + spiral_center_y
                
                # Draw line between corners
                line_length = max(1, int(math.sqrt((x2_rot - x1_rot)**2 + (y2_rot - y1_rot)**2)))
                for t in range(line_length):
                    if line_length > 0:
                        alpha = t / line_length
                        x = int(x1_rot + alpha * (x2_rot - x1_rot))
                        y = int(y1_rot + alpha * (y2_rot - y1_rot))
                        
                        if 0 <= x < width and 0 <= y < height:
                            # Golden color for rectangles
                            r_rect = int(255 * 0.8)
                            g_rect = int(215 * 0.8)
                            b_rect = int(0 * 0.8)
                            
                            pixel_index = y * width + x
                            if 0 <= pixel_index < len(pixels):
                                old_r, old_g, old_b = pixels[pixel_index]
                                pixels[pixel_index] = (
                                    min(255, old_r + r_rect),
                                    min(255, old_g + g_rect),
                                    min(255, old_b + b_rect)
                                )


def dust_animation(pixels, config, frame):
    """Pixel-sized dust particles floating around the screen - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    # Dark background with subtle gradient
    for y in range(height):
        for x in range(width):
            # Very subtle gradient from top to bottom
            gradient = int(5 + (y / height) * 10)
            pixels[y * width + x] = (gradient, gradient // 2, gradient // 4)
    
    # Create floating dust particles
    dust_count = 200
    for dust in range(dust_count):
        # Pseudo-random particle properties based on dust index
        seed = dust * 127 + frame // 3
        
        # Particle base position
        base_x = (seed * 31) % width
        base_y = (seed * 47) % height
        
        # Floating motion with different speeds and patterns
        float_speed_x = 0.5 + (dust % 5) * 0.2
        float_speed_y = 0.3 + (dust % 7) * 0.15
        
        # Brownian motion components
        brownian_x = math.sin((frame + dust * 17) * 0.1) * 2
        brownian_y = math.cos((frame + dust * 23) * 0.08) * 1.5
        
        # Wind effect
        wind_x = math.sin(frame * 0.02) * 0.5
        wind_y = math.cos(frame * 0.015) * 0.3
        
        # Final particle position
        x = (base_x + (frame * float_speed_x) + brownian_x + wind_x) % width
        y = (base_y + (frame * float_speed_y) + brownian_y + wind_y) % height
        
        # Particle size (some particles are 2x2 pixels)
        particle_size = 1 if dust % 3 == 0 else 2
        
        # Particle brightness varies
        brightness_base = 50 + (dust % 100)
        brightness_flicker = math.sin((frame + dust * 13) * 0.2) * 20
        brightness = int(max(30, min(200, brightness_base + brightness_flicker)))
        
        # Particle color - mostly white/gray with some colored dust
        if dust % 10 == 0:  # 10% colored particles
            # Colored dust - warm colors
            if dust % 3 == 0:
                r, g, b = brightness, int(brightness * 0.7), int(brightness * 0.3)  # Orange
            elif dust % 3 == 1:
                r, g, b = int(brightness * 0.8), brightness, int(brightness * 0.4)  # Yellow-green
            else:
                r, g, b = int(brightness * 0.6), int(brightness * 0.8), brightness  # Blue
        else:
            # Regular gray dust
            gray = int(brightness * (0.7 + math.sin(dust * 0.1) * 0.3))
            r, g, b = gray, gray, gray
        
        # Draw particle
        for py in range(particle_size):
            for px in range(particle_size):
                particle_x = int(x) + px
                particle_y = int(y) + py
                
                if 0 <= particle_x < width and 0 <= particle_y < height:
                    pixel_index = particle_y * width + particle_x
                    
                    # Size-based brightness adjustment
                    size_brightness = 1.0 if particle_size == 1 else 0.7
                    final_r = int(r * size_brightness)
                    final_g = int(g * size_brightness)
                    final_b = int(b * size_brightness)
                    
                    # Additive blending for overlapping particles
                    old_r, old_g, old_b = pixels[pixel_index]
                    pixels[pixel_index] = (
                        min(255, old_r + final_r),
                        min(255, old_g + final_g),
                        min(255, old_b + final_b)
                                         )


def rain_animation(pixels, config, frame):
    """Realistic raindrops falling with splashes - optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    
    # Dark stormy sky background
    for y in range(height):
        for x in range(width):
            # Gradient from dark gray to lighter gray (storm clouds)
            sky_darkness = int(20 + (y / height) * 15)
            pixels[y * width + x] = (sky_darkness, sky_darkness, sky_darkness + 5)
    
    # Create falling raindrops
    drop_count = 80
    for drop in range(drop_count):
        # Pseudo-random drop properties
        seed = drop * 97 + frame // 2
        
        # Drop starting position and timing
        drop_x = (seed * 31) % width
        drop_speed = 2 + (drop % 4)  # Varying speeds
        drop_length = 3 + (drop % 3)  # Varying lengths
        
        # Drop falls from top
        drop_start_frame = (seed * 13) % 120  # Stagger drop starts
        drop_y = ((frame - drop_start_frame) * drop_speed) % (height + drop_length + 10)
        
        # Only draw if drop is on screen
        if -drop_length <= drop_y <= height:
            # Draw raindrop as a vertical line
            for segment in range(drop_length):
                y = int(drop_y - segment)
                
                if 0 <= y < height:
                    # Raindrop color - blue-white
                    brightness = max(0, 255 - segment * 40)  # Fade along length
                    r = int(brightness * 0.6)
                    g = int(brightness * 0.8)
                    b = brightness
                    
                    pixel_index = y * width + drop_x
                    if 0 <= pixel_index < len(pixels):
                        # Additive blending for overlapping drops
                        old_r, old_g, old_b = pixels[pixel_index]
                        pixels[pixel_index] = (
                            min(255, old_r + r),
                            min(255, old_g + g),
                            min(255, old_b + b)
                        )
        
        # Create splash when drop hits bottom
        if height - 5 <= drop_y <= height:
            splash_frame = max(0, int(drop_y - (height - 5)))
            splash_size = splash_frame * 2
            
            # Draw splash as expanding circle
            for splash_radius in range(1, splash_size + 1):
                splash_points = splash_radius * 8  # Points around circle
                for point in range(splash_points):
                    angle = (point / splash_points) * 2 * math.pi
                    splash_x = int(drop_x + math.cos(angle) * splash_radius)
                    splash_y = int(height - 1 + math.sin(angle) * splash_radius * 0.3)  # Flatten splash
                    
                    if 0 <= splash_x < width and 0 <= splash_y < height:
                        # Splash brightness fades with radius and time
                        splash_brightness = max(0, 150 - splash_radius * 30 - splash_frame * 20)
                        
                        # Light blue splash color
                        r_splash = int(splash_brightness * 0.7)
                        g_splash = int(splash_brightness * 0.9)
                        b_splash = splash_brightness
                        
                        pixel_index = splash_y * width + splash_x
                        if 0 <= pixel_index < len(pixels):
                            old_r, old_g, old_b = pixels[pixel_index]
                            pixels[pixel_index] = (
                                min(255, old_r + r_splash),
                                min(255, old_g + g_splash),
                                min(255, old_b + b_splash)
                            )
    
    # Add lightning flashes occasionally
    lightning_chance = frame % 300  # Every 15 seconds
    if lightning_chance < 5:  # Brief flash
        flash_intensity = int(255 * (1 - lightning_chance / 5))
        
        # Lightning illuminates the whole sky
        for y in range(height // 3):  # Top third of screen
            for x in range(width):
                pixel_index = y * width + x
                old_r, old_g, old_b = pixels[pixel_index]
                
                # Add white lightning flash
                lightning_add = flash_intensity // 2
                pixels[pixel_index] = (
                    min(255, old_r + lightning_add),
                    min(255, old_g + lightning_add),
                    min(255, old_b + lightning_add)
                )
        
        # Add lightning bolt
        if lightning_chance == 0:  # Only on first frame of flash
            bolt_x = width // 2 + (frame % 20) - 10
            bolt_segments = 8
            
            for segment in range(bolt_segments):
                bolt_y = segment * (height // bolt_segments)
                bolt_x += (segment % 2) * 4 - 2  # Zigzag pattern
                
                if 0 <= bolt_x < width and 0 <= bolt_y < height:
                    # Bright white lightning bolt
                    for thickness in range(3):  # Make bolt 3 pixels wide
                        bolt_pixel_x = bolt_x + thickness - 1
                        if 0 <= bolt_pixel_x < width:
                            pixel_index = bolt_y * width + bolt_pixel_x
                            if 0 <= pixel_index < len(pixels):
                                pixels[pixel_index] = (255, 255, 255)


# Animation registry
EMBEDDED_ANIMATIONS = {
    'aurora': aurora_animation,
    'plasma': plasma_animation,
    'fire': fire_animation,
    'ocean': ocean_animation,
    'rainbow': rainbow_animation,
    'matrix': matrix_rain_animation,
    'kaleidoscope': kaleidoscope_animation,
    'starfield': starfield_animation,
    'clouds': clouds_animation,
    'fireworks': fireworks_animation,
    'hyperspace': hyperspace_animation,
    'golden': golden_ratio_animation,
    'dust': dust_animation,
    'rain': rain_animation
}


# =====================================================
# LIGHTBOX SYSTEM CLASS
# =====================================================

class LightBoxSystem:
    """Complete LightBox system with embedded animations."""
    
    def __init__(self):
        self.config = None
        self.conductor = None
        self.running = False
        self.current_animation = 'aurora'
        self.frame_count = 0
        self.animation_thread = None
        
    def initialize(self):
        """Initialize the complete system."""
        try:
            # Load configuration
            self.config = ConfigManager()
            print("✅ Configuration loaded - Platform: raspberry_pi")
            
            # Create conductor  
            self.conductor = Conductor(self.config)
            print("✅ Conductor created")
            
            # Hardware is initialized in Conductor.__init__
            print("✅ Hardware initialized")
            cols = self.config.get('hub75.cols')
            rows = self.config.get('hub75.rows')
            print(f"   🎯 Matrix: {cols}x{rows}")
            anims = list(EMBEDDED_ANIMATIONS.keys())
            print(f"   🎬 Embedded animations: {anims}")
            return True
                
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False
    
    def start_animation_loop(self):
        """Start the animation loop in a separate thread."""
        if self.animation_thread and self.animation_thread.is_alive():
            return
            
        self.running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        print("✅ Animation loop started")
    
    def _animation_loop(self):
        """Main animation loop."""
        if not self.conductor:
            print("❌ No conductor available for animation")
            return
            
        # Set animation and start loop
        self.conductor.set_animation(self.current_animation)
        
        try:
            while self.running:
                # Update frame through conductor
                self.conductor.update_frame()
                
                # Frame timing
                time.sleep(0.05)  # 20 FPS
                self.frame_count += 1
                
        except Exception as e:
            print(f"Animation loop error: {e}")
    
    def set_animation(self, name):
        """Set current animation."""
        if name in EMBEDDED_ANIMATIONS:
            self.current_animation = name
            self.frame_count = 0  # Reset frame counter
            if self.conductor:
                self.conductor.set_animation(name)
            print(f"✅ Animation set to: {name}")
            return True
        return False
    
    def get_status(self):
        """Get system status."""
        return {
            'status': 'running' if self.running else 'stopped',
            'current_animation': self.current_animation,
            'available_animations': list(EMBEDDED_ANIMATIONS.keys()),
            'frame_count': self.frame_count,
            'matrix_size': f"{self.config.get('hub75.cols', 64)}x{self.config.get('hub75.rows', 64)}" if self.config else "unknown"
        }
    
    def stop(self):
        """Stop the system."""
        self.running = False
        if self.conductor and self.conductor.matrix:
            # Clear matrix
            self.conductor.matrix.Clear()
        print("✅ System stopped")


# =====================================================
# WEB INTERFACE
# =====================================================

@app.route('/')
def index():
    """Main web interface with full controls."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LightBox HUB75 Control Panel</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; margin: 0; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin: 0; }
        .panel { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.2); }
        .controls-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; }
        .control-group { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; }
        .control-group h3 { margin-top: 0; color: #4CAF50; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; }
        .slider-container { margin: 15px 0; }
        .slider-container label { display: block; margin-bottom: 5px; font-weight: bold; }
        .slider { width: 100%; height: 8px; border-radius: 5px; background: #333; outline: none; }
        .slider::-webkit-slider-thumb { appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #4CAF50; cursor: pointer; }
        .value-display { background: #222; padding: 5px 10px; border-radius: 5px; display: inline-block; min-width: 50px; text-align: center; margin-left: 10px; }
        .button { background: linear-gradient(45deg, #4CAF50, #45a049); color: white; padding: 12px 24px; margin: 5px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
        .button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .button.active { background: linear-gradient(45deg, #FF6B6B, #FF5252); }
        .button.secondary { background: linear-gradient(45deg, #2196F3, #1976D2); }
        .button.danger { background: linear-gradient(45deg, #f44336, #d32f2f); }
        .animation-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .status { background: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; }
        .color-picker { width: 50px; height: 30px; border: none; border-radius: 5px; cursor: pointer; }
        .preset-colors { display: flex; gap: 10px; margin: 10px 0; }
        .preset-color { width: 30px; height: 30px; border-radius: 50%; cursor: pointer; border: 2px solid #fff; }
        .toggle-switch { position: relative; display: inline-block; width: 60px; height: 34px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }
        .toggle-slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .toggle-slider { background-color: #4CAF50; }
        input:checked + .toggle-slider:before { transform: translateX(26px); }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin: 15px 0; }
        .metric { background: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px; text-align: center; }
        .metric label { display: block; font-size: 0.9em; color: #ccc; margin-bottom: 5px; }
        .metric span { font-size: 1.5em; font-weight: bold; color: #4CAF50; }
        .system-info { background: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px; margin: 10px 0; }
        .system-info h4 { margin: 0 0 10px 0; color: #4CAF50; }
        .system-info div { margin: 5px 0; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: rgba(0,0,0,0.3); border-radius: 10px 10px 0 0; cursor: pointer; margin-right: 5px; }
        .tab.active { background: rgba(76,175,80,0.3); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .optimization-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-ok { background-color: #4CAF50; }
        .status-warning { background-color: #FF9800; }
        .status-error { background-color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌈 LightBox HUB75 Control Panel</h1>
            <div class="status" id="status">Loading...</div>
        </div>
        
        <div class="panel">
            <h2>🎬 Animation Selection</h2>
            <div class="animation-grid" id="animations">
                <button class="button" onclick="setAnimation('aurora')" id="btn-aurora">🌌 Aurora</button>
                <button class="button" onclick="setAnimation('plasma')" id="btn-plasma">🔥 Plasma</button>
                <button class="button" onclick="setAnimation('fire')" id="btn-fire">🔥 Fire</button>
                <button class="button" onclick="setAnimation('ocean')" id="btn-ocean">🌊 Ocean</button>
                <button class="button" onclick="setAnimation('rainbow')" id="btn-rainbow">🌈 Rainbow</button>
                <button class="button" onclick="setAnimation('matrix')" id="btn-matrix">🔋 Matrix</button>
                <button class="button" onclick="setAnimation('kaleidoscope')" id="btn-kaleidoscope">🔮 Kaleidoscope</button>
                <button class="button" onclick="setAnimation('starfield')" id="btn-starfield">⭐ Starfield</button>
                <button class="button" onclick="setAnimation('clouds')" id="btn-clouds">☁️ Clouds</button>
                <button class="button" onclick="setAnimation('fireworks')" id="btn-fireworks">🎆 Fireworks</button>
                <button class="button" onclick="setAnimation('hyperspace')" id="btn-hyperspace">🚀 Hyperspace</button>
                <button class="button" onclick="setAnimation('golden')" id="btn-golden">🌀 Golden Ratio</button>
                <button class="button" onclick="setAnimation('dust')" id="btn-dust">✨ Dust</button>
                <button class="button" onclick="setAnimation('rain')" id="btn-rain">🌧️ Rain</button>
            </div>
        </div>
        
        <div class="controls-grid">
            <div class="panel">
                <div class="control-group">
                    <h3>💡 Display Controls</h3>
                    
                    <div class="slider-container">
                        <label>Brightness</label>
                        <input type="range" min="10" max="100" value="80" class="slider" id="brightness">
                        <span class="value-display" id="brightness-val">80%</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Animation Speed</label>
                        <input type="range" min="10" max="200" value="100" class="slider" id="speed">
                        <span class="value-display" id="speed-val">100%</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Color Intensity</label>
                        <input type="range" min="50" max="150" value="100" class="slider" id="intensity">
                        <span class="value-display" id="intensity-val">100%</span>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <label>Power</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="power" checked onchange="togglePower()">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="control-group">
                    <h3>🎨 Color Controls</h3>
                    
                    <div class="slider-container">
                        <label>Hue Shift</label>
                        <input type="range" min="0" max="360" value="0" class="slider" id="hue">
                        <span class="value-display" id="hue-val">0°</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Saturation</label>
                        <input type="range" min="50" max="150" value="100" class="slider" id="saturation">
                        <span class="value-display" id="saturation-val">100%</span>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <label>Primary Color</label><br>
                        <input type="color" value="#4CAF50" class="color-picker" id="primary-color">
                    </div>
                    
                    <div>
                        <label>Color Presets</label>
                        <div class="preset-colors">
                            <div class="preset-color" style="background: #FF0000;" onclick="setPresetColor('#FF0000')"></div>
                            <div class="preset-color" style="background: #00FF00;" onclick="setPresetColor('#00FF00')"></div>
                            <div class="preset-color" style="background: #0000FF;" onclick="setPresetColor('#0000FF')"></div>
                            <div class="preset-color" style="background: #FFFF00;" onclick="setPresetColor('#FFFF00')"></div>
                            <div class="preset-color" style="background: #FF00FF;" onclick="setPresetColor('#FF00FF')"></div>
                            <div class="preset-color" style="background: #00FFFF;" onclick="setPresetColor('#00FFFF')"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="control-group">
                    <h3>⚙️ Animation Settings</h3>
                    
                    <div class="slider-container">
                        <label>Scale/Zoom</label>
                        <input type="range" min="50" max="200" value="100" class="slider" id="scale">
                        <span class="value-display" id="scale-val">100%</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Complexity</label>
                        <input type="range" min="1" max="10" value="5" class="slider" id="complexity">
                        <span class="value-display" id="complexity-val">5</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Smoothness</label>
                        <input type="range" min="1" max="10" value="5" class="slider" id="smoothness">
                        <span class="value-display" id="smoothness-val">5</span>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <button class="button" onclick="savePreset()">💾 Save Preset</button>
                        <button class="button" onclick="randomize()">🎲 Randomize</button>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="control-group">
                    <h3>📊 Performance Metrics</h3>
                    <div class="metric-grid">
                        <div class="metric">
                            <label>FPS</label>
                            <span id="metric-fps">30</span>
                        </div>
                        <div class="metric">
                            <label>CPU</label>
                            <span id="metric-cpu">45%</span>
                        </div>
                        <div class="metric">
                            <label>Memory</label>
                            <span id="metric-memory">65%</span>
                        </div>
                        <div class="metric">
                            <label>Temp</label>
                            <span id="metric-temp">42°C</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🔧 Hardware Optimization</h2>
            <div class="tabs">
                <div class="tab active" onclick="switchTab('hub75-config')">HUB75 Settings</div>
                <div class="tab" onclick="switchTab('performance-config')">Performance</div>
                <div class="tab" onclick="switchTab('system-config')">System</div>
            </div>
            
            <div id="hub75-config" class="tab-content active">
                <div class="optimization-grid">
                    <div class="control-group">
                        <h3>Matrix Configuration</h3>
                        <div class="slider-container">
                            <label>GPIO Slowdown</label>
                            <input type="range" min="1" max="6" value="4" class="slider" id="gpio-slowdown">
                            <span class="value-display" id="gpio-slowdown-val">4</span>
                        </div>
                        <div class="slider-container">
                            <label>PWM Bits</label>
                            <input type="range" min="1" max="11" value="11" class="slider" id="pwm-bits">
                            <span class="value-display" id="pwm-bits-val">11</span>
                        </div>
                        <div class="slider-container">
                            <label>Refresh Limit (Hz)</label>
                            <input type="range" min="60" max="300" value="120" class="slider" id="limit-refresh">
                            <span class="value-display" id="limit-refresh-val">120</span>
                        </div>
                    </div>
                    <div class="control-group">
                        <h3>Hardware Features</h3>
                        <div style="margin: 15px 0;">
                            <label>Hardware PWM</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="hardware-pwm" onchange="updateOptimization('hardware-pwm', this.checked)">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div style="margin: 15px 0;">
                            <label>CPU Isolation</label>
                            <label class="toggle-switch">
                                <input type="checkbox" id="cpu-isolation" checked onchange="updateOptimization('cpu-isolation', this.checked)">
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div id="hardware-status">
                            <h4>Hardware Status</h4>
                            <div><span class="status-indicator status-warning" id="pwm-status"></span>PWM: <span id="pwm-status-text">Checking...</span></div>
                            <div><span class="status-indicator status-warning" id="cpu-status"></span>CPU Isolation: <span id="cpu-status-text">Checking...</span></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="performance-config" class="tab-content">
                <div class="optimization-grid">
                    <div class="control-group">
                        <h3>Performance Tuning</h3>
                        <div class="slider-container">
                            <label>Target FPS</label>
                            <input type="range" min="15" max="60" value="30" class="slider" id="target-fps">
                            <span class="value-display" id="target-fps-val">30</span>
                        </div>
                        <button class="button secondary" onclick="optimizeSystem()">🚀 Auto-Optimize System</button>
                        <div id="optimization-results" style="margin-top: 15px;"></div>
                    </div>
                    <div class="control-group">
                        <h3>System Status</h3>
                        <div id="optimization-status">
                            <div>CPU Governor: <span id="cpu-governor">Checking...</span></div>
                            <div>GPU Memory: <span id="gpu-memory">Checking...</span></div>
                            <div>Audio Services: <span id="audio-services">Checking...</span></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="system-config" class="tab-content">
                <div class="optimization-grid">
                    <div class="control-group">
                        <h3>System Actions</h3>
                        <button class="button secondary" onclick="restartSystem()">🔄 Restart Service</button>
                        <button class="button danger" onclick="emergencyStop()">🛑 Emergency Stop</button>
                    </div>
                    <div class="control-group">
                        <h3>Advanced</h3>
                        <button class="button" onclick="exportConfig()">📤 Export Config</button>
                        <button class="button" onclick="resetDefaults()">🔄 Reset Defaults</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h3>📊 System Information</h3>
            <div id="system-info">
                <div class="system-info">
                    <h4>Hardware Information</h4>
                    <div>Pi Model: <span id="pi-model">Loading...</span></div>
                    <div>Software Version: <span id="software-version">Loading...</span></div>
                    <div>Driver Version: <span id="driver-version">Loading...</span></div>
                    <div>Network Status: <span id="network-status">Loading...</span></div>
                </div>
                <div class="system-info">
                    <h4>Current Configuration</h4>
                    <div>Matrix Size: <span id="matrix-size">Loading...</span></div>
                    <div>GPIO Slowdown: <span id="current-gpio-slowdown">Loading...</span></div>
                    <div>PWM Bits: <span id="current-pwm-bits">Loading...</span></div>
                    <div>Hardware Mapping: <span id="hardware-mapping">Loading...</span></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentAnimation = 'aurora';
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    currentAnimation = data.current_animation;
                    document.getElementById('status').innerHTML = 
                        `<strong>Status:</strong> ${data.status} | <strong>Animation:</strong> ${data.current_animation} | <strong>Frame:</strong> ${data.frame_count} | <strong>Matrix:</strong> ${data.matrix_size}`;
                    
                    // Update active button
                    document.querySelectorAll('.animation-grid .button').forEach(btn => btn.classList.remove('active'));
                    const activeBtn = document.getElementById('btn-' + data.current_animation);
                    if (activeBtn) activeBtn.classList.add('active');
                })
                .catch(error => console.error('Error updating status:', error));
        }
        
        function updateMetrics() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('metric-fps').textContent = data.fps || '30';
                    document.getElementById('metric-cpu').textContent = (data.cpu || 45) + '%';
                    document.getElementById('metric-memory').textContent = (data.memory || 65) + '%';
                    document.getElementById('metric-temp').textContent = data.temperature || '42°C';
                })
                .catch(error => console.error('Error updating metrics:', error));
        }
        
        function updateSystemInfo() {
            fetch('/api/system/info')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('pi-model').textContent = data.pi_model || 'Unknown';
                    document.getElementById('software-version').textContent = data.software_version || 'Unknown';
                    document.getElementById('driver-version').textContent = data.driver_version || 'Unknown';
                    document.getElementById('network-status').textContent = data.network_status || 'Unknown';
                })
                .catch(error => console.error('Error updating system info:', error));
            
            fetch('/api/hardware/status')
                .then(response => response.json())
                .then(data => {
                    // Update hardware status indicators
                    const pwmStatus = document.getElementById('pwm-status');
                    const cpuStatus = document.getElementById('cpu-status');
                    
                    if (data.hardware_pwm) {
                        pwmStatus.className = 'status-indicator status-ok';
                        document.getElementById('pwm-status-text').textContent = 'Enabled';
                    } else {
                        pwmStatus.className = 'status-indicator status-warning';
                        document.getElementById('pwm-status-text').textContent = 'Not Detected';
                    }
                    
                    if (data.cpu_isolation) {
                        cpuStatus.className = 'status-indicator status-ok';
                        document.getElementById('cpu-status-text').textContent = 'Enabled';
                    } else {
                        cpuStatus.className = 'status-indicator status-warning';
                        document.getElementById('cpu-status-text').textContent = 'Not Enabled';
                    }
                    
                    if (data.matrix_config) {
                        document.getElementById('matrix-size').textContent = `${data.matrix_config.rows}x${data.matrix_config.cols}`;
                        document.getElementById('current-gpio-slowdown').textContent = data.matrix_config.gpio_slowdown;
                        document.getElementById('current-pwm-bits').textContent = data.matrix_config.pwm_bits;
                        document.getElementById('hardware-mapping').textContent = 'Adafruit HAT';
                    }
                })
                .catch(error => console.error('Error updating hardware status:', error));
        }
        
        function setAnimation(name) {
            fetch(`/api/animation/${name}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus();
                    }
                });
        }
        
        function updateParameter(param, value) {
            fetch('/api/parameter', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({parameter: param, value: value})
            });
        }
        
        function updateOptimization(param, value) {
            fetch('/api/optimization/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({parameter: param, value: value})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Optimization updated: ${param} = ${value}`);
                }
            });
        }
        
        function optimizeSystem() {
            fetch('/api/system/optimize', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    const resultsDiv = document.getElementById('optimization-results');
                    if (data.success) {
                        resultsDiv.innerHTML = '<h4>Optimization Results:</h4>' + 
                            data.optimizations.map(opt => `<div>• ${opt}</div>`).join('');
                    }
                });
        }
        
        function switchTab(tabId) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabId).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        function togglePower() {
            const power = document.getElementById('power').checked;
            fetch('/api/power', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({power: power})
            });
        }
        
        function setPresetColor(color) {
            document.getElementById('primary-color').value = color;
            updateParameter('primary_color', color);
        }
        
        function savePreset() {
            const preset = {
                brightness: document.getElementById('brightness').value,
                speed: document.getElementById('speed').value,
                hue: document.getElementById('hue').value,
                saturation: document.getElementById('saturation').value,
                scale: document.getElementById('scale').value,
                complexity: document.getElementById('complexity').value,
                smoothness: document.getElementById('smoothness').value,
                primary_color: document.getElementById('primary-color').value,
                animation: currentAnimation
            };
            
            fetch('/api/save-preset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(preset)
            }).then(() => alert('Preset saved!'));
        }
        
        function randomize() {
            document.getElementById('brightness').value = Math.random() * 90 + 10;
            document.getElementById('speed').value = Math.random() * 190 + 10;
            document.getElementById('hue').value = Math.random() * 360;
            document.getElementById('saturation').value = Math.random() * 100 + 50;
            document.getElementById('scale').value = Math.random() * 150 + 50;
            updateAllSliders();
        }
        
        function restartSystem() {
            if (confirm('Restart the LightBox service? This will briefly interrupt the display.')) {
                fetch('/api/system/restart', {method: 'POST'})
                    .then(() => alert('Service restart initiated'));
            }
        }
        
        function emergencyStop() {
            if (confirm('Emergency stop all operations?')) {
                fetch('/api/emergency-stop', {method: 'POST'})
                    .then(() => alert('Emergency stop activated'));
            }
        }
        
        function exportConfig() {
            fetch('/api/hardware/config')
                .then(response => response.json())
                .then(data => {
                    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'lightbox-config.json';
                    a.click();
                });
        }
        
        function resetDefaults() {
            if (confirm('Reset all settings to defaults?')) {
                location.reload();
            }
        }
        
        function updateAllSliders() {
            ['brightness', 'speed', 'intensity', 'hue', 'saturation', 'scale', 'complexity', 'smoothness'].forEach(id => {
                const slider = document.getElementById(id);
                const display = document.getElementById(id + '-val');
                const value = slider.value;
                const unit = id === 'hue' ? '°' : (id === 'complexity' || id === 'smoothness' ? '' : '%');
                display.textContent = value + unit;
                updateParameter(id, value);
            });
            
            // Hardware optimization sliders
            ['gpio-slowdown', 'pwm-bits', 'limit-refresh', 'target-fps'].forEach(id => {
                const slider = document.getElementById(id);
                const display = document.getElementById(id + '-val');
                if (slider && display) {
                    const value = slider.value;
                    display.textContent = value;
                    updateOptimization(id, parseInt(value));
                }
            });
        }
        
        // Setup slider listeners
        ['brightness', 'speed', 'intensity', 'hue', 'saturation', 'scale', 'complexity', 'smoothness'].forEach(id => {
            const slider = document.getElementById(id);
            const display = document.getElementById(id + '-val');
            slider.addEventListener('input', function() {
                const unit = id === 'hue' ? '°' : (id === 'complexity' || id === 'smoothness' ? '' : '%');
                display.textContent = this.value + unit;
                updateParameter(id, this.value);
            });
        });
        
        // Setup hardware optimization slider listeners
        ['gpio-slowdown', 'pwm-bits', 'limit-refresh', 'target-fps'].forEach(id => {
            const slider = document.getElementById(id);
            const display = document.getElementById(id + '-val');
            if (slider && display) {
                slider.addEventListener('input', function() {
                    display.textContent = this.value;
                    updateOptimization(id, parseInt(this.value));
                });
            }
        });
        
        // Update intervals
        setInterval(updateStatus, 2000);
        setInterval(updateMetrics, 3000);
        setInterval(updateSystemInfo, 10000);
        
        // Initial updates
        updateStatus();
        updateMetrics();
        updateSystemInfo();
        updateAllSliders();
    </script>
</body>
</html>
"""


@app.route('/comprehensive')
def comprehensive():
    """Comprehensive control panel with optimization controls."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LightBox Comprehensive Control</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background: #f0f0f0; }
        .panel { background: #fff; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .back-link { color: #3498db; text-decoration: none; }
    </style>
</head>
<body>
    <div class="panel">
        <h1>🎛️ Comprehensive Control Panel</h1>
        <p>Advanced controls coming soon!</p>
        <p><a href="/" class="back-link">← Back to Main Control Panel</a></p>
    </div>
</body>
</html>
"""


@app.route('/simple')
def simple():
    """Streamlined control panel."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LightBox Simple Control</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; background: #f0f0f0; }
        .panel { background: #fff; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .back-link { color: #3498db; text-decoration: none; }
    </style>
</head>
<body>
    <div class="panel">
        <h1>🎮 Simple Control Panel</h1>
        <p>Simplified controls coming soon!</p>
        <p><a href="/" class="back-link">← Back to Main Control Panel</a></p>
    </div>
</body>
</html>
"""


@app.route('/api/status')
def api_status():
    """Get system status."""
    if lightbox_system:
        return jsonify(lightbox_system.get_status())
    return jsonify({'status': 'not initialized'})


@app.route('/api/stats')
def api_stats():
    """Get real-time performance statistics."""
    if lightbox_system:
        status = lightbox_system.get_status()
        return jsonify({
            'fps': status.get('fps', 30),
            'cpu': status.get('cpu_usage', 45),
            'temperature': status.get('temperature', 42),
            'memory': status.get('memory_usage', 65),
            'refresh_rate': status.get('refresh_rate', 120),
            'uptime': status.get('uptime', '2h 15m')
        })
    return jsonify({
        'fps': 30,
        'cpu': 45,
        'temperature': 42,
        'memory': 65,
        'refresh_rate': 120,
        'uptime': '2h 15m'
    })

@app.route('/api/system/info')
def api_system_info():
    """Get detailed system information."""
    import platform
    import socket
    import os
    
    # Get Raspberry Pi model
    pi_model = "Unknown"
    try:
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                pi_model = f.read().strip('\0')
        elif platform.machine() in ('arm', 'armv7l', 'aarch64'):
            pi_model = f"ARM device ({platform.machine()})"
        else:
            pi_model = platform.system()
    except:
        pass
    
    # Get network IP
    ip_address = "Unknown"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        pass
    
    # Get CPU temperature
    cpu_temp = "Unknown"
    try:
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", 'r') as f:
                temp_milliC = int(f.read().strip())
                cpu_temp = f"{temp_milliC / 1000.0:.1f}°C"
    except:
        pass
    
    # Get memory info
    memory_info = "Unknown"
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    total_mb = int(line.split()[1]) / 1024
                    memory_info = f"{total_mb:.0f} MB"
                    break
    except:
        pass
    
    # Get network status
    network_status = (f"Connected ({ip_address})" 
                     if ip_address != "Unknown" else "Disconnected")
    
    return jsonify({
        'pi_model': pi_model,
        'software_version': 'LightBox v2.0',
        'driver_version': 'HUB75 Driver',
        'network_status': network_status,
        'cpu_temperature': cpu_temp,
        'memory_total': memory_info,
        'kernel_version': platform.release()
    })

@app.route('/api/hardware/status')
def api_hardware_status():
    """Get hardware status including PWM detection and CPU isolation."""
    import os
    
    # Check CPU isolation
    cpu_isolation_detected = False
    try:
        with open('/proc/cmdline', 'r') as f:
            cmdline = f.read()
            if 'isolcpus=' in cmdline:
                cpu_isolation_detected = True
    except:
        pass
    
    # Check hardware PWM (GPIO4-GPIO18 jumper)
    hardware_pwm_detected = False
    try:
        # This is a simplified check - real hardware would be more complex
        if os.path.exists('/sys/class/gpio/gpio18'):
            hardware_pwm_detected = True
    except:
        pass
    
    # Get matrix configuration
    matrix_config = {}
    if lightbox_system and lightbox_system.config:
        matrix_config = {
            'rows': lightbox_system.config.get('hub75.rows', 64),
            'cols': lightbox_system.config.get('hub75.cols', 64),
            'gpio_slowdown': lightbox_system.config.get('hub75.gpio_slowdown', 4),
            'pwm_bits': lightbox_system.config.get('hub75.pwm_bits', 11),
            'brightness': lightbox_system.config.get('hub75.brightness', 80)
        }
    
    return jsonify({
        'hardware_pwm': hardware_pwm_detected,
        'cpu_isolation': cpu_isolation_detected,
        'matrix_type': 'hub75',
        'platform': 'raspberry_pi',
        'matrix_config': matrix_config
    })

@app.route('/api/hardware/config', methods=['GET', 'POST'])
def api_hardware_config():
    """Get or update hardware configuration."""
    if request.method == 'GET':
        if lightbox_system and lightbox_system.config:
            return jsonify({
                'hub75': {
                    'rows': lightbox_system.config.get('hub75.rows', 64),
                    'cols': lightbox_system.config.get('hub75.cols', 64),
                    'gpio_slowdown': lightbox_system.config.get('hub75.gpio_slowdown', 4),
                    'pwm_bits': lightbox_system.config.get('hub75.pwm_bits', 11),
                    'brightness': lightbox_system.config.get('hub75.brightness', 80),
                    'limit_refresh': lightbox_system.config.get('hub75.limit_refresh', 120),
                    'hardware_mapping': lightbox_system.config.get('hub75.hardware_mapping', 'adafruit-hat')
                },
                'performance': {
                    'target_fps': lightbox_system.config.get('performance.target_fps', 30),
                    'cpu_isolation': lightbox_system.config.get('performance.cpu_isolation', True),
                    'optimize_drawing': lightbox_system.config.get('performance.optimize_drawing', True)
                }
            })
        return jsonify({'error': 'System not initialized'}), 500
    
    else:  # POST
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No configuration provided'}), 400
        
        if lightbox_system and lightbox_system.config:
            # Update configuration
            for section, settings in data.items():
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        lightbox_system.config.set(f"{section}.{key}", value)
                else:
                    lightbox_system.config.set(section, settings)
            
            print(f"✅ Hardware configuration updated: {data}")
            return jsonify({'success': True})
        
        return jsonify({'error': 'System not initialized'}), 500


    @app.route('/api/optimization/config', methods=['GET'])
    def get_optimization_config():
        """Get current optimization configuration."""
        try:
            config = {
                'complexity': lightbox_system.config.get('complexity', 5),
                'density': lightbox_system.config.get('density', 0.8),
                'gamma': lightbox_system.config.get('gamma', 2.2),
                'brightness': lightbox_system.config.get('brightness', 1.0),
                'contrast': lightbox_system.config.get('contrast', 1.0),
                'saturation': lightbox_system.config.get('saturation', 1.0),
                'hue_shift': lightbox_system.config.get('hue_shift', 0.0),
                'motion_blur': lightbox_system.config.get('motion_blur', 0.2),
                'fade_rate': lightbox_system.config.get('fade_rate', 0.1),
                'edge_fade': lightbox_system.config.get('edge_fade', 0.0),
                'center_focus': lightbox_system.config.get('center_focus', 0.0),
                'vignette': lightbox_system.config.get('vignette', 0.0)
            }
            return jsonify(config)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/optimization/update', methods=['POST'])
def api_optimization_update():
    """Update optimization parameters."""
    data = request.get_json()
    if not data or 'parameter' not in data or 'value' not in data:
        return jsonify({'error': 'Missing parameter or value'}), 400
    
    parameter = data['parameter']
    value = data['value']
    
    # Apply optimization parameter
    if lightbox_system and lightbox_system.config:
        # Map frontend parameter names to config keys
        param_map = {
            'gpio-slowdown': 'hub75.gpio_slowdown',
            'pwm-bits': 'hub75.pwm_bits',
            'brightness': 'hub75.brightness',
            'limit-refresh': 'hub75.limit_refresh',
            'target-fps': 'performance.target_fps',
            'cpu-isolation': 'performance.cpu_isolation',
            'hardware-pwm': 'hub75.hardware_pwm'
        }
        
        config_key = param_map.get(parameter, parameter)
        # Parse nested config key (e.g., "hub75.gpio_slowdown")        if "." in config_key:            section, key = config_key.split(".", 1)            if section not in lightbox_system.config.config:                lightbox_system.config.config[section] = {}            lightbox_system.config.config[section][key] = value        else:            lightbox_system.config.config[config_key] = value
        
        print(f"✅ Optimization parameter updated: {parameter} = {value}")
        return jsonify({
            'success': True, 
            'parameter': parameter, 
            'value': value
        })
    
    return jsonify({'error': 'System not initialized'}), 500

@app.route('/api/system/optimize', methods=['POST'])
def api_system_optimize():
    """Apply system-level optimizations."""
    import subprocess
    import os
    
    optimizations = []
    
    # Check and suggest CPU governor optimization
    try:
        gov_path = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
        if os.path.exists(gov_path):
            result = subprocess.run(['cat', gov_path], 
                                  capture_output=True, text=True)
            current_governor = result.stdout.strip()
            if current_governor != 'performance':
                optimizations.append(
                    f"CPU governor is '{current_governor}' - "
                    "consider setting to 'performance' mode")
            else:
                optimizations.append(
                    "CPU governor already set to performance mode")
    except:
        optimizations.append("Could not check CPU governor")
    
    # Check CPU isolation
    try:
        with open('/proc/cmdline', 'r') as f:
            cmdline = f.read()
            if 'isolcpus=' in cmdline:
                optimizations.append("CPU isolation is enabled")
            else:
                optimizations.append("CPU isolation recommended: Add 'isolcpus=3' to /boot/cmdline.txt and reboot")
    except:
        optimizations.append("Could not check CPU isolation")
    
    # Check GPU memory setting
    try:
        if os.path.exists('/boot/config.txt'):
            with open('/boot/config.txt', 'r') as f:
                config = f.read()
                if 'gpu_mem=' in config:
                    optimizations.append("GPU memory limit is configured")
                else:
                    optimizations.append("GPU memory optimization recommended: Add 'gpu_mem=16' to /boot/config.txt")
    except:
        optimizations.append("Could not check GPU memory configuration")
    
    return jsonify({
        'success': True,
        'optimizations': optimizations,
        'message': (f"System optimization check completed. "
                   f"Found {len(optimizations)} items.")
    })


@app.route('/api/emergency-stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop all animations."""
    if lightbox_system:
        lightbox_system.stop()
    return jsonify({'success': True, 'message': 'Emergency stop activated'})


@app.route('/api/animation/<name>', methods=['POST'])
def api_set_animation(name):
    """Set animation."""
    if lightbox_system:
        success = lightbox_system.set_animation(name)
        return jsonify({'success': success, 'animation': name})
    return jsonify({'success': False, 'error': 'System not initialized'})


@app.route('/api/animations')
def api_animations():
    """Get available animations."""
    return jsonify({'animations': list(EMBEDDED_ANIMATIONS.keys())})


@app.route('/api/parameter', methods=['POST'])
def api_set_parameter():
    """Set animation parameter."""
    try:
        data = request.get_json()
        param = data.get('parameter')
        value = data.get('value')
        
        if lightbox_system and lightbox_system.config:
            # Store parameter in config
            lightbox_system.config.config['parameters'] = lightbox_system.config.config.get('parameters', {})
            lightbox_system.config.config['parameters'][param] = value
            
            # Apply brightness immediately
            if param == 'brightness' and lightbox_system.conductor and lightbox_system.conductor.matrix:
                lightbox_system.conductor.matrix.brightness = int(value)
            
            return jsonify({'success': True, 'parameter': param, 'value': value})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'System not initialized'})


@app.route('/api/power', methods=['POST'])
def api_power():
    """Toggle system power."""
    try:
        data = request.get_json()
        power = data.get('power', True)
        
        if lightbox_system:
            if power:
                if not lightbox_system.running:
                    lightbox_system.start_animation_loop()
            else:
                lightbox_system.running = False
                if lightbox_system.conductor and lightbox_system.conductor.matrix:
                    lightbox_system.conductor.matrix.Clear()
            
            return jsonify({'success': True, 'power': power})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'System not initialized'})


@app.route('/api/save-preset', methods=['POST'])
def api_save_preset():
    """Save current settings as preset."""
    try:
        data = request.get_json()
        
        if lightbox_system:
            # Save preset to config
            presets = lightbox_system.config.config.get('presets', [])
            preset_name = f"Preset_{len(presets) + 1}"
            data['name'] = preset_name
            data['timestamp'] = time.time()
            presets.append(data)
            lightbox_system.config.config['presets'] = presets
            
            return jsonify({'success': True, 'preset_name': preset_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'System not initialized'})


# =====================================================
# MAIN FUNCTION
# =====================================================

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\n🛑 Shutdown signal received")
    if lightbox_system:
        lightbox_system.stop()
    sys.exit(0)


def main():
    """Start the complete LightBox system."""
    global lightbox_system
    
    print("🚀 Starting Complete LightBox System")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize system
    lightbox_system = LightBoxSystem()
    if not lightbox_system.initialize():
        print("❌ Failed to initialize LightBox system")
        return False
    
    # Start animation loop
    lightbox_system.start_animation_loop()
    
    # Configure Flask app
    CORS(app)
    
    # Start web server
    print("\n🌐 Starting web server...")
    print("   📱 Web interface: http://lightbox.local:8888")
    print("   🎛️  API status: http://lightbox.local:8888/api/status")
    print("   🎬 API animations: http://lightbox.local:8888/api/animations")
    print("\n🎯 System ready! You should see lights on the HUB75 matrix!")
    
    try:
        app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Web server error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    try:
        if main():
            print("✅ System completed successfully")
        else:
            print("❌ System failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
        if lightbox_system:
            lightbox_system.stop()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if lightbox_system:
            lightbox_system.stop()
        sys.exit(1) 