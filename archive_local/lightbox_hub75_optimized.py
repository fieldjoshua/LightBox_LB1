#!/usr/bin/env python3
"""
🌈 LIGHTBOX HUB75 OPTIMIZED - UNIFIED EDITION
=============================================

Complete LightBox system optimized for HUB75 RGB matrices.
Combines the best elements from all working versions:

✅ Core Operational Stability (from lightbox_complete_original.py)
✅ HUB75 Anti-Jitter Optimizations (gpio_slowdown, PWM settings)  
✅ Gamma Correction & Image Quality (from lightbox_complete_fixed.py)
✅ 14 Embedded Animations (Aurora, Plasma, Fire, Ocean, etc.)
✅ Comprehensive Web Interface & API
✅ Dynamic Animation Parameters System
✅ Hardware Detection & Monitoring
✅ Real-time Performance Metrics

Hardware Support:
- HUB75 RGB LED Matrices (optimized for 64x64)
- Raspberry Pi 3B+/4 with Adafruit RGB Matrix HAT
- Hardware PWM detection and configuration
- Anti-jitter timing optimizations

Created: 2025-01-15
Author: LightBox Development Team
Version: HUB75-Optimized-Unified
"""

import math
import os
import signal
import subprocess
import sys
import threading
import time

# Flask web interface
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

# =====================================================
# HARDWARE DETECTION & OPTIMIZATION UTILITIES
# =====================================================

def detect_hardware_pwm():
    """Detect if GPIO4-GPIO18 hardware PWM jumper is installed."""
    try:
        # Check if hardware PWM is available by testing GPIO access
        result = subprocess.run(['gpio', 'readall'], capture_output=True, text=True)
        if 'gpio: command not found' not in result.stderr:
            # Additional check for hardware PWM capability
            try:
                with open('/sys/kernel/debug/pwm') as f:
                    pwm_info = f.read()
                    return 'pwm' in pwm_info.lower()
            except:
                pass
        return False
    except Exception:
        return False

def check_pi_version():
    """Detect Raspberry Pi model for optimal configuration."""
    try:
        with open('/proc/cpuinfo') as f:
            for line in f:
                if 'Model' in line:
                    return line.strip()
        return "Unknown Pi Model"
    except:
        return "Development Environment"

def detect_cpu_isolation():
    """Check if CPU isolation is configured."""
    try:
        with open('/proc/cmdline') as f:
            cmdline = f.read()
            return 'isolcpus' in cmdline
    except:
        return False

# =====================================================
# IMAGE QUALITY & GAMMA CORRECTION
# =====================================================

def apply_gamma_correction(r, g, b, gamma=2.2):
    """Apply gamma correction for accurate color reproduction on HUB75."""
    if gamma == 1.0:
        return r, g, b

    # Normalize to 0-1 range
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    # Apply gamma correction
    r_corrected = pow(r_norm, 1.0/gamma)
    g_corrected = pow(g_norm, 1.0/gamma)
    b_corrected = pow(b_norm, 1.0/gamma)

    # Convert back to 0-255 range
    return (
        min(255, int(r_corrected * 255)),
        min(255, int(g_corrected * 255)),
        min(255, int(b_corrected * 255))
    )

def apply_black_level_correction(r, g, b, black_level=2):
    """Ensure true black rendering by applying black level correction."""
    if r <= black_level and g <= black_level and b <= black_level:
        return 0, 0, 0  # True black
    return r, g, b

def apply_brightness_correction(r, g, b, brightness=1.0):
    """Apply brightness scaling with proper clipping."""
    return (
        min(255, int(r * brightness)),
        min(255, int(g * brightness)),
        min(255, int(b * brightness))
    )

# =====================================================
# OPTIMIZED CONFIGURATION MANAGER
# =====================================================

class OptimizedConfigManager:
    """Configuration manager with HUB75 optimizations and dynamic parameters."""

    def __init__(self):
        # Detect hardware for optimal configuration
        self.pi_version = check_pi_version()
        self.has_hardware_pwm = detect_hardware_pwm()
        self.has_cpu_isolation = detect_cpu_isolation()

        print("🔍 Hardware Detection:")
        print(f"   📱 {self.pi_version}")
        print(f"   ⚡ Hardware PWM: {'✅' if self.has_hardware_pwm else '❌'}")
        print(f"   🏃 CPU Isolation: {'✅' if self.has_cpu_isolation else '❌'}")

        # Optimal HUB75 configuration based on hardware
        self.config = {
            "platform": "raspberry_pi",
            "matrix_type": "hub75",
            "target_fps": 30,

            # HUB75 Hardware Configuration
            "hub75": {
                "rows": 64,
                "cols": 64,
                "chain_length": 1,
                "parallel": 1,
                "hardware_mapping": "adafruit-hat",

                # ⚡ ANTI-JITTER OPTIMIZATION SETTINGS ⚡
                # These settings prioritize smooth animation over color depth
                "gpio_slowdown": 2,  # Reduced from 4 for better timing
                "pwm_bits": 8,       # Reduced from 11 for higher refresh rate
                "pwm_lsb_nanoseconds": 100,  # Faster timing (was 130)
                "pwm_dither_bits": 2,        # Compensate for lower PWM bits
                "limit_refresh": 150,        # Higher refresh rate

                # Hardware PWM (best quality if available)
                "disable_hardware_pulsing": not self.has_hardware_pwm,

                # Panel optimizations
                "scan_mode": 0,
                "row_address_type": 0,
                "multiplexing": 0,
                "show_refresh_rate": False,  # Disable for performance

                # Brightness and gamma
                "brightness": 80,  # 0-100%
                "gamma": 2.2,      # Standard gamma correction
                "black_level": 2,  # True black threshold
            },

            # Animation Parameters (Dynamic)
            "animation": {
                "current": "aurora",
                "speed": 1.0,
                "brightness": 0.8,
                "complexity": 5,
                "density": 0.8,
                "scale": 1.0,
                "hue_shift": 0.0,
                "saturation": 1.0,
                "contrast": 1.0,
                "motion_blur": 0.1,
                "fade_rate": 0.05,
            },

            # Performance monitoring
            "monitoring": {
                "enabled": True,
                "fps_target": 30,
                "cpu_threshold": 80,
                "temp_threshold": 75,
            }
        }

    def get(self, key, default=None):
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_animation_params(self):
        """Get all animation parameters as a flat dictionary."""
        return self.config["animation"].copy()

    def update_animation_params(self, params):
        """Update animation parameters from dictionary."""
        for key, value in params.items():
            if key in self.config["animation"]:
                self.config["animation"][key] = value

# =====================================================
# OPTIMIZED MATRIX CONTROLLER
# =====================================================

class OptimizedMatrixController:
    """High-performance HUB75 matrix controller with anti-jitter optimizations."""

    def __init__(self, config):
        self.config = config
        self.matrix = None
        self.canvas = None

        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
        self.cpu_usage = 0
        self.temperature = 0

        # Thread safety
        self._render_lock = threading.Lock()

        # Initialize hardware
        self._initialize_hardware()

    def _initialize_hardware(self):
        """Initialize HUB75 matrix with optimized settings."""
        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions

            options = RGBMatrixOptions()

            # Basic configuration
            options.rows = self.config.get('hub75.rows', 64)
            options.cols = self.config.get('hub75.cols', 64)
            options.chain_length = self.config.get('hub75.chain_length', 1)
            options.parallel = self.config.get('hub75.parallel', 1)
            options.hardware_mapping = self.config.get('hub75.hardware_mapping', 'adafruit-hat')

            # 🚀 CRITICAL ANTI-JITTER SETTINGS 🚀
            options.gpio_slowdown = self.config.get('hub75.gpio_slowdown', 2)
            options.pwm_bits = self.config.get('hub75.pwm_bits', 8)
            options.pwm_lsb_nanoseconds = self.config.get('hub75.pwm_lsb_nanoseconds', 100)
            options.pwm_dither_bits = self.config.get('hub75.pwm_dither_bits', 2)

            # Hardware PWM for stability
            options.disable_hardware_pulsing = self.config.get('hub75.disable_hardware_pulsing', True)

            # Refresh rate limiting
            limit_refresh = self.config.get('hub75.limit_refresh', 150)
            if hasattr(options, 'limit_refresh_rate_hz'):
                options.limit_refresh_rate_hz = limit_refresh

            # Advanced panel settings
            options.scan_mode = self.config.get('hub75.scan_mode', 0)
            options.row_address_type = self.config.get('hub75.row_address_type', 0)
            options.multiplexing = self.config.get('hub75.multiplexing', 0)
            options.show_refresh_rate = self.config.get('hub75.show_refresh_rate', False)

            # Brightness
            options.brightness = self.config.get('hub75.brightness', 80)

            # Create matrix
            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()

            print("✅ HUB75 Matrix initialized:")
            print(f"   📐 Resolution: {options.cols}x{options.rows}")
            print(f"   ⚡ GPIO Slowdown: {options.gpio_slowdown}")
            print(f"   🎨 PWM Bits: {options.pwm_bits}")
            print(f"   ⏱️  PWM Timing: {options.pwm_lsb_nanoseconds}ns")
            print(f"   🔧 PWM Dither: {options.pwm_dither_bits}")
            print(f"   🔄 Refresh Limit: {limit_refresh}Hz")
            print(f"   🔆 Brightness: {options.brightness}%")
            print(f"   ⚡ Hardware PWM: {'✅' if not options.disable_hardware_pulsing else '❌'}")

        except ImportError:
            print("⚠️  RGB Matrix library not available - using simulation mode")
            self.matrix = None
            self.canvas = None
        except Exception as e:
            print(f"❌ Matrix initialization failed: {e}")
            self.matrix = None
            self.canvas = None

    def render_pixels(self, pixels):
        """Render pixel array to matrix with image quality corrections."""
        with self._render_lock:
            if not self.matrix or not self.canvas:
                return

            # Get image quality settings
            gamma = self.config.get('hub75.gamma', 2.2)
            black_level = self.config.get('hub75.black_level', 2)
            brightness = self.config.get('animation.brightness', 0.8)

            # Clear canvas
            self.canvas.Clear()

            # Render pixels with quality corrections
            width = self.config.get('hub75.cols', 64)
            height = self.config.get('hub75.rows', 64)

            for y in range(height):
                for x in range(width):
                    pixel_index = y * width + x
                    if pixel_index < len(pixels):
                        r, g, b = pixels[pixel_index]

                        # Apply image quality corrections
                        r, g, b = apply_brightness_correction(r, g, b, brightness)
                        r, g, b = apply_gamma_correction(r, g, b, gamma)
                        r, g, b = apply_black_level_correction(r, g, b, black_level)

                        self.canvas.SetPixel(x, y, r, g, b)

            # Swap buffers for smooth animation
            self.canvas = self.matrix.SwapOnVSync(self.canvas)

            # Update performance metrics
            self._update_performance_metrics()

    def _update_performance_metrics(self):
        """Update FPS and performance metrics."""
        current_time = time.time()
        self.frame_count += 1

        # Calculate FPS every second
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time

            # Update system metrics
            self._update_system_metrics()

    def _update_system_metrics(self):
        """Update CPU usage and temperature."""
        try:
            # CPU usage
            with os.popen('top -bn1 | grep "Cpu(s)"') as f:
                cpu_line = f.read()
                if '%us' in cpu_line:
                    self.cpu_usage = float(cpu_line.split('%us')[0].split()[-1])
        except:
            pass

        try:
            # Temperature (Raspberry Pi)
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                self.temperature = int(f.read()) / 1000.0
        except:
            pass

    def get_performance_metrics(self):
        """Get current performance metrics."""
        return {
            'fps': round(self.fps, 1),
            'cpu_usage': round(self.cpu_usage, 1),
            'temperature': round(self.temperature, 1),
            'frame_count': self.frame_count
        }

# =====================================================
# EMBEDDED ANIMATIONS - ALL 14 OPTIMIZED FOR HUB75
# =====================================================

def aurora_animation(pixels, config, frame):
    """Aurora Borealis - Flowing northern lights optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    # Get dynamic parameters
    params = config.get_animation_params()
    speed = params.get('speed', 1.0)
    complexity = params.get('complexity', 5)
    hue_shift = params.get('hue_shift', 0.0)

    for y in range(height):
        for x in range(width):
            # Multiple wave layers for aurora effect
            wave1 = math.sin(x * 0.1 + frame * 0.02 * speed) * 0.5
            wave2 = math.sin(x * 0.05 + y * 0.1 + frame * 0.03 * speed) * 0.3
            wave3 = math.sin(x * 0.08 + y * 0.05 + frame * 0.015 * speed) * 0.2

            # Combine waves
            combined = wave1 + wave2 + wave3

            # Aurora curtain effect
            curtain_factor = math.exp(-(y - height * 0.3) ** 2 / (height * 0.4))
            aurora_strength = max(0, combined * curtain_factor)

            # Color shifting (green to blue to purple)
            hue_base = (x / width + hue_shift) % 1.0
            if hue_base < 0.33:  # Green
                r = int(aurora_strength * 50)
                g = int(aurora_strength * 255)
                b = int(aurora_strength * 100)
            elif hue_base < 0.66:  # Blue
                r = int(aurora_strength * 100)
                g = int(aurora_strength * 150)
                b = int(aurora_strength * 255)
            else:  # Purple
                r = int(aurora_strength * 200)
                g = int(aurora_strength * 50)
                b = int(aurora_strength * 255)

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def plasma_animation(pixels, config, frame):
    """Plasma - Psychedelic color waves optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Create plasma pattern with multiple sine waves
            plasma = (
                math.sin(x / 8.0 + frame * 0.1 * speed) +
                math.sin(y / 6.0 + frame * 0.08 * speed) +
                math.sin((x + y) / 12.0 + frame * 0.05 * speed) +
                math.sin(math.sqrt(x*x + y*y) / 10.0 + frame * 0.03 * speed)
            )

            # Normalize to 0-1
            plasma = (plasma + 4) / 8

            # Create RGB from plasma value
            hue = plasma * 2 * math.pi
            r = int(128 + 127 * math.sin(hue))
            g = int(128 + 127 * math.sin(hue + 2 * math.pi / 3))
            b = int(128 + 127 * math.sin(hue + 4 * math.pi / 3))

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def fire_animation(pixels, config, frame):
    """Fire - Flickering flames optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Fire starts hot at bottom, cools toward top
            heat_factor = 1.0 - (y / height)

            # Turbulence effect
            turbulence = (
                math.sin(x * 0.1 + frame * 0.08 * speed) * 0.3 +
                math.sin(x * 0.05 + y * 0.1 + frame * 0.1 * speed) * 0.2 +
                math.sin(x * 0.2 + frame * 0.15 * speed) * 0.1
            )

            # Combine heat and turbulence
            fire_intensity = max(0, heat_factor + turbulence * 0.5)

            # Fire colors (red to yellow to white)
            if fire_intensity > 0.8:
                r, g, b = 255, 255, int(fire_intensity * 200)
            elif fire_intensity > 0.5:
                r, g, b = 255, int(fire_intensity * 255), 0
            elif fire_intensity > 0.2:
                r, g, b = int(fire_intensity * 255), int(fire_intensity * 100), 0
            else:
                r, g, b = int(fire_intensity * 100), 0, 0

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def ocean_animation(pixels, config, frame):
    """Ocean - Rolling waves optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Multiple wave layers
            wave1 = math.sin(x * 0.1 + frame * 0.05 * speed) * 0.4
            wave2 = math.sin(x * 0.15 + frame * 0.03 * speed) * 0.3
            wave3 = math.sin(x * 0.08 + y * 0.1 + frame * 0.04 * speed) * 0.2

            # Combine waves
            water_level = height * 0.6 + (wave1 + wave2 + wave3) * height * 0.2

            if y > water_level:
                # Deep water
                depth = (y - water_level) / (height - water_level)
                r = int(10 + depth * 30)
                g = int(50 + depth * 100)
                b = int(100 + depth * 155)
            else:
                # Sky/foam
                r = int(150 + (1 - y / water_level) * 105)
                g = int(200 + (1 - y / water_level) * 55)
                b = 255

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def rainbow_animation(pixels, config, frame):
    """Rainbow - Moving rainbow patterns optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Moving rainbow pattern
            hue = (x + frame * speed) / width
            hue = hue % 1.0  # Keep in 0-1 range

            # Convert HSV to RGB
            h = hue * 6
            c = 1.0  # Full saturation
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

            # Brightness gradient
            brightness = 0.5 + 0.5 * math.sin(y * 0.1 + frame * 0.05 * speed)

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (
                    int(r * 255 * brightness),
                    int(g * 255 * brightness),
                    int(b * 255 * brightness)
                )

def matrix_rain_animation(pixels, config, frame):
    """Matrix Rain - Digital rain effect optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)
    density = params.get('density', 0.8)

    # Clear to black
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 0)

    # Create multiple rain streams
    stream_count = int(width * density)
    for stream in range(stream_count):
        # Stream position
        x = (stream * 3) % width

        # Stream progress
        stream_y = (frame * speed + stream * 10) % (height + 20)

        # Draw stream
        for i in range(10):  # Stream length
            y = int(stream_y - i)
            if 0 <= y < height:
                # Fade intensity along stream
                intensity = max(0, 1 - i / 10.0)

                # Green matrix color
                g = int(255 * intensity)
                r = int(100 * intensity)

                pixel_index = y * width + x
                if pixel_index < len(pixels):
                    pixels[pixel_index] = (r, g, 0)

def kaleidoscope_animation(pixels, config, frame):
    """Kaleidoscope - Rotating geometric patterns optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Convert to polar coordinates
            dx = x - center_x
            dy = y - center_y
            angle = math.atan2(dy, dx)
            radius = math.sqrt(dx*dx + dy*dy)

            # Rotating pattern
            rotated_angle = angle + frame * 0.05 * speed

            # Kaleidoscope segments
            segments = 6
            segment_angle = (rotated_angle % (2 * math.pi / segments)) * segments

            # Color based on angle and radius
            hue = (segment_angle + radius * 0.1) % (2 * math.pi)
            intensity = 0.5 + 0.5 * math.sin(radius * 0.2 + frame * 0.03 * speed)

            r = int(128 + 127 * math.sin(hue) * intensity)
            g = int(128 + 127 * math.sin(hue + 2 * math.pi / 3) * intensity)
            b = int(128 + 127 * math.sin(hue + 4 * math.pi / 3) * intensity)

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def starfield_animation(pixels, config, frame):
    """Starfield - 3D space flight optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    # Clear to black space
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 5)  # Deep space

    # Create stars
    star_count = 100
    for star in range(star_count):
        # Pseudo-random star positions
        seed = star * 73
        star_x = (seed * 31) % 200 - 100  # -100 to 100
        star_y = (seed * 47) % 200 - 100
        star_z = (seed * 13) % 50 + 1     # 1 to 50

        # Move star towards viewer
        z = star_z - (frame * speed) % 50
        if z <= 0:
            z = 50

        # Project 3D to 2D
        screen_x = int(center_x + star_x * 32 / z)
        screen_y = int(center_y + star_y * 32 / z)

        # Check bounds and draw star
        if 0 <= screen_x < width and 0 <= screen_y < height:
            # Star brightness based on distance
            brightness = int(255 * (1 - z / 50))

            pixel_index = screen_y * width + screen_x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (brightness, brightness, brightness)

def clouds_animation(pixels, config, frame):
    """Clouds - Peaceful clouds in blue sky optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    for y in range(height):
        for x in range(width):
            # Blue sky gradient
            sky_factor = 1.0 - (y / height) * 0.3
            base_r = int(100 * sky_factor)
            base_g = int(150 * sky_factor)
            base_b = int(255 * sky_factor)

            # Cloud layers
            cloud_density = 0

            # Large slow clouds
            cloud1_x = (x + frame * 0.5 * speed) % (width * 2)
            cloud1 = math.sin(cloud1_x * 0.1) * math.sin(y * 0.15)
            cloud_density += max(0, cloud1 - 0.3) * 2

            # Smaller faster clouds
            cloud2_x = (x + frame * 0.8 * speed) % (width * 1.5)
            cloud2 = math.sin(cloud2_x * 0.15) * math.sin(y * 0.2)
            cloud_density += max(0, cloud2 - 0.5) * 1.5

            # Apply clouds
            cloud_factor = min(1, cloud_density)
            if cloud_factor > 0:
                cloud_r = int(255 * cloud_factor)
                cloud_g = int(255 * cloud_factor)
                cloud_b = int(230 * cloud_factor)

                r = int(base_r * (1 - cloud_factor) + cloud_r * cloud_factor)
                g = int(base_g * (1 - cloud_factor) + cloud_g * cloud_factor)
                b = int(base_b * (1 - cloud_factor) + cloud_b * cloud_factor)
            else:
                r, g, b = base_r, base_g, base_b

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def fireworks_animation(pixels, config, frame):
    """Fireworks - Exploding fireworks optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    # Dark night sky
    for i in range(len(pixels)):
        pixels[i] = (5, 5, 15)

    # Multiple fireworks
    firework_count = 3
    for fw in range(firework_count):
        fw_time = (frame * speed + fw * 60) % 180
        fw_x = 20 + fw * 20
        fw_y = 15 + fw * 15

        if fw_time < 120:  # Active firework
            explosion_radius = min(25, fw_time * 0.3)

            # Burst particles
            for p in range(24):
                angle = (p / 24) * 2 * math.pi
                px = fw_x + math.cos(angle) * explosion_radius
                py = fw_y + math.sin(angle) * explosion_radius

                if 0 <= px < width and 0 <= py < height:
                    fade = max(0, 1 - fw_time / 120)

                    # Different colors per firework
                    if fw == 0:
                        r, g, b = int(255 * fade), int(100 * fade), int(50 * fade)
                    elif fw == 1:
                        r, g, b = int(100 * fade), int(255 * fade), int(50 * fade)
                    else:
                        r, g, b = int(200 * fade), int(200 * fade), int(255 * fade)

                    pixel_index = int(py) * width + int(px)
                    if pixel_index < len(pixels):
                        old_r, old_g, old_b = pixels[pixel_index]
                        pixels[pixel_index] = (
                            min(255, old_r + r),
                            min(255, old_g + g),
                            min(255, old_b + b)
                        )

def hyperspace_animation(pixels, config, frame):
    """Hyperspace - Flying through space optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    # Clear to deep space
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 5)

    # High-speed starfield
    for star in range(150):
        seed = star * 73
        star_x = (seed * 31) % 200 - 100
        star_y = (seed * 47) % 200 - 100
        star_z = (seed * 13) % 50 + 1

        # Fast movement
        z = star_z - (frame * speed * 2) % 50
        if z <= 0:
            z = 50

        # Project and draw trail
        screen_x = int(center_x + star_x * 32 / z)
        screen_y = int(center_y + star_y * 32 / z)

        if 0 <= screen_x < width and 0 <= screen_y < height:
            brightness = int(255 * (1 - z / 50))

            # Draw star trail
            for trail in range(3):
                trail_z = z + trail * 2
                if trail_z > 0:
                    trail_x = int(center_x + star_x * 32 / trail_z)
                    trail_y = int(center_y + star_y * 32 / trail_z)

                    if 0 <= trail_x < width and 0 <= trail_y < height:
                        trail_brightness = max(0, brightness - trail * 80)
                        pixel_index = trail_y * width + trail_x

                        if pixel_index < len(pixels):
                            pixels[pixel_index] = (
                                int(trail_brightness * 0.8),
                                int(trail_brightness * 0.9),
                                trail_brightness
                            )

def golden_ratio_animation(pixels, config, frame):
    """Golden Ratio - Mathematical spirals optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)
    center_x = width // 2
    center_y = height // 2

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    # Clear to black
    for i in range(len(pixels)):
        pixels[i] = (0, 0, 0)

    # Golden ratio spiral
    phi = (1 + math.sqrt(5)) / 2  # Golden ratio

    for t in range(200):
        # Spiral parameters
        angle = t * 0.1 + frame * 0.02 * speed
        radius = t * 0.3

        # Golden spiral
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))

        if 0 <= x < width and 0 <= y < height:
            # Color based on position along spiral
            hue = (t * 0.05 + frame * 0.01 * speed) % (2 * math.pi)
            intensity = max(0, 1 - t / 200)

            r = int(128 + 127 * math.sin(hue) * intensity)
            g = int(128 + 127 * math.sin(hue + 2 * math.pi / 3) * intensity)
            b = int(128 + 127 * math.sin(hue + 4 * math.pi / 3) * intensity)

            pixel_index = y * width + x
            if pixel_index < len(pixels):
                pixels[pixel_index] = (r, g, b)

def dust_animation(pixels, config, frame):
    """Dust - Floating particles optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)
    density = params.get('density', 0.8)

    # Dark background
    for i in range(len(pixels)):
        pixels[i] = (10, 10, 20)

    # Floating dust particles
    particle_count = int(100 * density)
    for p in range(particle_count):
        # Particle position with slow movement
        seed = p * 67
        px = ((seed * 31 + frame * speed * 0.5) % (width * 100)) / 100
        py = ((seed * 47 + frame * speed * 0.3) % (height * 100)) / 100

        # Particle brightness flicker
        flicker = 0.5 + 0.5 * math.sin(p + frame * 0.1 * speed)
        brightness = int(150 * flicker)

        x, y = int(px), int(py)
        if 0 <= x < width and 0 <= y < height:
            pixel_index = y * width + x
            if pixel_index < len(pixels):
                # Golden dust color
                pixels[pixel_index] = (brightness, int(brightness * 0.8), int(brightness * 0.3))

def rain_animation(pixels, config, frame):
    """Rain - Raindrops with lightning optimized for HUB75."""
    width = config.get('hub75.cols', 64)
    height = config.get('hub75.rows', 64)

    params = config.get_animation_params()
    speed = params.get('speed', 1.0)

    # Dark stormy sky
    for i in range(len(pixels)):
        pixels[i] = (20, 20, 40)

    # Rain drops
    for drop in range(50):
        seed = drop * 59
        drop_x = (seed * 31) % width
        drop_y = ((seed * 13 + frame * speed * 3) % (height + 20)) - 10

        # Draw raindrop trail
        for trail in range(5):
            y = int(drop_y - trail)
            if 0 <= y < height:
                intensity = max(0, 1 - trail / 5)
                blue = int(150 * intensity)

                pixel_index = y * width + drop_x
                if pixel_index < len(pixels):
                    old_r, old_g, old_b = pixels[pixel_index]
                    pixels[pixel_index] = (
                        old_r,
                        old_g + int(50 * intensity),
                        min(255, old_b + blue)
                    )

    # Lightning flashes
    lightning_chance = frame % 300
    if lightning_chance < 5:
        flash_intensity = int(200 * (5 - lightning_chance) / 5)

        # Light up top third of screen
        for y in range(height // 3):
            for x in range(width):
                pixel_index = y * width + x
                old_r, old_g, old_b = pixels[pixel_index]

                lightning_add = flash_intensity // 2
                pixels[pixel_index] = (
                    min(255, old_r + lightning_add),
                    min(255, old_g + lightning_add),
                    min(255, old_b + lightning_add)
                )

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
    """Complete LightBox system optimized for HUB75 with all features."""

    def __init__(self):
        self.config = None
        self.controller = None
        self.running = False
        self.current_animation = 'aurora'
        self.frame_count = 0
        self.animation_thread = None
        self.pixels = None

        # Performance monitoring
        self.start_time = time.time()
        self.total_frames = 0

    def initialize(self):
        """Initialize the complete system."""
        try:
            print("🌈 LIGHTBOX HUB75 OPTIMIZED - UNIFIED EDITION")
            print("=" * 50)

            # Load optimized configuration
            self.config = OptimizedConfigManager()
            print("✅ Optimized configuration loaded")

            # Create optimized matrix controller
            self.controller = OptimizedMatrixController(self.config)
            print("✅ Optimized matrix controller created")

            # Initialize pixel buffer
            width = self.config.get('hub75.cols', 64)
            height = self.config.get('hub75.rows', 64)
            self.pixels = [(0, 0, 0)] * (width * height)
            print(f"✅ Pixel buffer initialized: {width}x{height}")

            # Display available animations
            animations = list(EMBEDDED_ANIMATIONS.keys())
            print(f"🎬 Embedded animations ({len(animations)}): {', '.join(animations)}")

            print("=" * 50)
            print("🚀 System ready for HUB75 optimization!")

            return True

        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False

    def start_animation(self, animation_name='aurora'):
        """Start the animation loop."""
        if animation_name not in EMBEDDED_ANIMATIONS:
            print(f"❌ Animation '{animation_name}' not found")
            return False

        self.current_animation = animation_name
        self.running = True
        self.frame_count = 0

        # Start animation thread
        self.animation_thread = threading.Thread(target=self._animation_loop)
        self.animation_thread.daemon = True
        self.animation_thread.start()

        print(f"🎬 Started animation: {animation_name}")
        return True

    def stop_animation(self):
        """Stop the animation loop."""
        self.running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
        print("⏹️  Animation stopped")

    def _animation_loop(self):
        """Main animation loop optimized for HUB75."""
        target_fps = self.config.get('target_fps', 30)
        frame_time = 1.0 / target_fps

        last_time = time.time()

        while self.running:
            current_time = time.time()

            # Run current animation
            if self.current_animation in EMBEDDED_ANIMATIONS:
                EMBEDDED_ANIMATIONS[self.current_animation](
                    self.pixels, self.config, self.frame_count
                )

                # Render to matrix
                self.controller.render_pixels(self.pixels)

                self.frame_count += 1
                self.total_frames += 1

            # Frame rate limiting
            elapsed = current_time - last_time
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            last_time = time.time()

    def set_animation(self, name):
        """Change the current animation."""
        if name in EMBEDDED_ANIMATIONS:
            self.current_animation = name
            self.frame_count = 0  # Reset for new animation
            print(f"🎬 Changed to animation: {name}")
            return True
        return False

    def update_animation_params(self, params):
        """Update animation parameters."""
        self.config.update_animation_params(params)
        print(f"🎛️  Updated animation parameters: {params}")

    def get_status(self):
        """Get system status."""
        uptime = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        metrics = self.controller.get_performance_metrics() if self.controller else {}

        return {
            'running': self.running,
            'current_animation': self.current_animation,
            'available_animations': list(EMBEDDED_ANIMATIONS.keys()),
            'frame_count': self.frame_count,
            'total_frames': self.total_frames,
            'uptime': round(uptime, 1),
            'matrix_size': f"{self.config.get('hub75.cols', 64)}x{self.config.get('hub75.rows', 64)}",
            'performance': metrics,
            'animation_params': self.config.get_animation_params(),
            'hardware': {
                'pi_model': self.config.pi_version,
                'hardware_pwm': self.config.has_hardware_pwm,
                'cpu_isolation': self.config.has_cpu_isolation,
            }
        }

# =====================================================
# WEB INTERFACE & API
# =====================================================

# Global system instance
lightbox_system = None

# Flask app
app = Flask(__name__)
CORS(app)

# Comprehensive web interface template
WEB_INTERFACE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌈 LightBox HUB75 Optimized Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .panel {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .panel h3 {
            margin-bottom: 15px;
            color: #FFD700;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 5px;
        }
        .animation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .animation-btn {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            border: none;
            border-radius: 10px;
            color: white;
            padding: 15px 10px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            text-transform: capitalize;
        }
        .animation-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .animation-btn.active {
            background: linear-gradient(45deg, #FFD700, #FFA500);
            transform: scale(1.05);
        }
        .control-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #FFD700;
        }
        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.3);
            outline: none;
            margin-bottom: 5px;
        }
        input[type="range"]::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #FFD700;
            cursor: pointer;
        }
        .value-display {
            background: rgba(0, 0, 0, 0.3);
            padding: 5px 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        .status-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .status-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #4ECDC4;
        }
        .control-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            color: white;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
            transition: all 0.3s ease;
        }
        .control-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        .hardware-info {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .performance-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 5px;
        }
        .performance-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ECDC4, #44A08D);
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌈 LightBox HUB75 Optimized Control</h1>
        
        <div class="grid">
            <!-- Animation Selection -->
            <div class="panel">
                <h3>🎬 Animation Selection</h3>
                <div class="animation-grid" id="animationGrid"></div>
                <div class="control-group">
                    <button class="control-btn" onclick="startAnimation()">▶️ Start</button>
                    <button class="control-btn" onclick="stopAnimation()">⏹️ Stop</button>
                </div>
            </div>
            
            <!-- Animation Parameters -->
            <div class="panel">
                <h3>🎛️ Animation Parameters</h3>
                <div class="control-group">
                    <label>Speed</label>
                    <input type="range" id="speed" min="0.1" max="3.0" step="0.1" value="1.0" onchange="updateParam('speed', this.value)">
                    <div class="value-display" id="speedValue">1.0x</div>
                </div>
                <div class="control-group">
                    <label>Brightness</label>
                    <input type="range" id="brightness" min="0.1" max="1.0" step="0.1" value="0.8" onchange="updateParam('brightness', this.value)">
                    <div class="value-display" id="brightnessValue">80%</div>
                </div>
                <div class="control-group">
                    <label>Complexity</label>
                    <input type="range" id="complexity" min="1" max="10" step="1" value="5" onchange="updateParam('complexity', this.value)">
                    <div class="value-display" id="complexityValue">5</div>
                </div>
                <div class="control-group">
                    <label>Density</label>
                    <input type="range" id="density" min="0.1" max="1.0" step="0.1" value="0.8" onchange="updateParam('density', this.value)">
                    <div class="value-display" id="densityValue">80%</div>
                </div>
            </div>
            
            <!-- System Status -->
            <div class="panel">
                <h3>📊 System Status</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div>Status</div>
                        <div class="status-value" id="systemStatus">●</div>
                    </div>
                    <div class="status-item">
                        <div>FPS</div>
                        <div class="status-value" id="currentFPS">--</div>
                        <div class="performance-bar">
                            <div class="performance-fill" id="fpsBar" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <div>CPU</div>
                        <div class="status-value" id="cpuUsage">--%</div>
                        <div class="performance-bar">
                            <div class="performance-fill" id="cpuBar" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <div>Temp</div>
                        <div class="status-value" id="temperature">--°C</div>
                        <div class="performance-bar">
                            <div class="performance-fill" id="tempBar" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <div>Frames</div>
                        <div class="status-value" id="frameCount">--</div>
                    </div>
                    <div class="status-item">
                        <div>Uptime</div>
                        <div class="status-value" id="uptime">--s</div>
                    </div>
                </div>
            </div>
            
            <!-- Hardware Information -->
            <div class="panel">
                <h3>🔧 Hardware Information</h3>
                <div class="hardware-info">
                    <div><strong>Matrix:</strong> <span id="matrixSize">--</span></div>
                    <div><strong>Pi Model:</strong> <span id="piModel">--</span></div>
                    <div><strong>Hardware PWM:</strong> <span id="hardwarePWM">--</span></div>
                    <div><strong>CPU Isolation:</strong> <span id="cpuIsolation">--</span></div>
                    <div><strong>Current Animation:</strong> <span id="currentAnimation">--</span></div>
                </div>
            </div>
            
            <!-- Advanced Controls -->
            <div class="panel">
                <h3>⚙️ Advanced Controls</h3>
                <div class="control-group">
                    <label>Hue Shift</label>
                    <input type="range" id="hueShift" min="0.0" max="1.0" step="0.1" value="0.0" onchange="updateParam('hue_shift', this.value)">
                    <div class="value-display" id="hueShiftValue">0%</div>
                </div>
                <div class="control-group">
                    <label>Saturation</label>
                    <input type="range" id="saturation" min="0.0" max="2.0" step="0.1" value="1.0" onchange="updateParam('saturation', this.value)">
                    <div class="value-display" id="saturationValue">100%</div>
                </div>
                <div class="control-group">
                    <label>Motion Blur</label>
                    <input type="range" id="motionBlur" min="0.0" max="1.0" step="0.1" value="0.1" onchange="updateParam('motion_blur', this.value)">
                    <div class="value-display" id="motionBlurValue">10%</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentAnimation = 'aurora';
        
        const animations = [
            'aurora', 'plasma', 'fire', 'ocean', 'rainbow', 'matrix',
            'kaleidoscope', 'starfield', 'clouds', 'fireworks', 
            'hyperspace', 'golden', 'dust', 'rain'
        ];
        
        // Initialize animation buttons
        function initializeAnimations() {
            const grid = document.getElementById('animationGrid');
            animations.forEach(anim => {
                const btn = document.createElement('button');
                btn.className = 'animation-btn';
                btn.textContent = anim;
                btn.onclick = () => selectAnimation(anim);
                btn.id = `anim-${anim}`;
                grid.appendChild(btn);
            });
            selectAnimation('aurora');
        }
        
        function selectAnimation(name) {
            currentAnimation = name;
            
            // Update button states
            animations.forEach(anim => {
                const btn = document.getElementById(`anim-${anim}`);
                btn.classList.toggle('active', anim === name);
            });
            
            // Send to server
            fetch('/api/animation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ animation: name })
            });
        }
        
        function startAnimation() {
            fetch('/api/start', { method: 'POST' });
        }
        
        function stopAnimation() {
            fetch('/api/stop', { method: 'POST' });
        }
        
        function updateParam(param, value) {
            // Update display
            const display = document.getElementById(param + 'Value');
            if (display) {
                if (param === 'brightness' || param === 'density') {
                    display.textContent = Math.round(value * 100) + '%';
                } else if (param === 'hue_shift') {
                    display.textContent = Math.round(value * 100) + '%';
                } else if (param === 'saturation') {
                    display.textContent = Math.round(value * 100) + '%';
                } else if (param === 'motion_blur') {
                    display.textContent = Math.round(value * 100) + '%';
                } else if (param === 'speed') {
                    display.textContent = value + 'x';
                } else {
                    display.textContent = value;
                }
            }
            
            // Send to server
            const params = {};
            params[param] = parseFloat(value);
            fetch('/api/params', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // System status
                    document.getElementById('systemStatus').textContent = data.running ? '🟢' : '🔴';
                    document.getElementById('currentAnimation').textContent = data.current_animation;
                    document.getElementById('frameCount').textContent = data.frame_count;
                    document.getElementById('uptime').textContent = data.uptime + 's';
                    document.getElementById('matrixSize').textContent = data.matrix_size;
                    
                    // Hardware info
                    if (data.hardware) {
                        document.getElementById('piModel').textContent = data.hardware.pi_model;
                        document.getElementById('hardwarePWM').textContent = data.hardware.hardware_pwm ? '✅' : '❌';
                        document.getElementById('cpuIsolation').textContent = data.hardware.cpu_isolation ? '✅' : '❌';
                    }
                    
                    // Performance metrics
                    if (data.performance) {
                        const fps = data.performance.fps || 0;
                        const cpu = data.performance.cpu_usage || 0;
                        const temp = data.performance.temperature || 0;
                        
                        document.getElementById('currentFPS').textContent = fps.toFixed(1);
                        document.getElementById('cpuUsage').textContent = cpu.toFixed(1) + '%';
                        document.getElementById('temperature').textContent = temp.toFixed(1) + '°C';
                        
                        // Update performance bars
                        document.getElementById('fpsBar').style.width = Math.min(100, (fps / 30) * 100) + '%';
                        document.getElementById('cpuBar').style.width = Math.min(100, cpu) + '%';
                        document.getElementById('tempBar').style.width = Math.min(100, (temp / 80) * 100) + '%';
                    }
                })
                .catch(err => console.error('Status update failed:', err));
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initializeAnimations();
            updateStatus();
            
            // Update status every 2 seconds
            setInterval(updateStatus, 2000);
        });
    </script>
</body>
</html>
'''

# API Routes
@app.route('/')
def index():
    """Main web interface."""
    return render_template_string(WEB_INTERFACE_HTML)

@app.route('/api/status')
def api_status():
    """Get system status."""
    if lightbox_system:
        return jsonify(lightbox_system.get_status())
    else:
        return jsonify({'error': 'System not initialized'}), 500

@app.route('/api/animations')
def api_animations():
    """Get available animations."""
    return jsonify({'animations': list(EMBEDDED_ANIMATIONS.keys())})

@app.route('/api/animation', methods=['POST'])
def api_set_animation():
    """Set current animation."""
    if not lightbox_system:
        return jsonify({'error': 'System not initialized'}), 500

    data = request.get_json()
    animation = data.get('animation')

    if lightbox_system.set_animation(animation):
        return jsonify({'success': True, 'animation': animation})
    else:
        return jsonify({'error': 'Invalid animation'}), 400

@app.route('/api/start', methods=['POST'])
def api_start():
    """Start animation."""
    if not lightbox_system:
        return jsonify({'error': 'System not initialized'}), 500

    if lightbox_system.start_animation(lightbox_system.current_animation):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to start'}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop animation."""
    if not lightbox_system:
        return jsonify({'error': 'System not initialized'}), 500

    lightbox_system.stop_animation()
    return jsonify({'success': True})

@app.route('/api/params', methods=['POST'])
def api_update_params():
    """Update animation parameters."""
    if not lightbox_system:
        return jsonify({'error': 'System not initialized'}), 500

    data = request.get_json()
    lightbox_system.update_animation_params(data)
    return jsonify({'success': True, 'params': data})

@app.route('/api/optimization/config')
def api_optimization_config():
    """Get optimization configuration."""
    if not lightbox_system:
        return jsonify({'error': 'System not initialized'}), 500

    return jsonify({
        'hub75_config': {
            'gpio_slowdown': lightbox_system.config.get('hub75.gpio_slowdown'),
            'pwm_bits': lightbox_system.config.get('hub75.pwm_bits'),
            'pwm_lsb_nanoseconds': lightbox_system.config.get('hub75.pwm_lsb_nanoseconds'),
            'pwm_dither_bits': lightbox_system.config.get('hub75.pwm_dither_bits'),
            'limit_refresh': lightbox_system.config.get('hub75.limit_refresh'),
            'hardware_pwm_enabled': not lightbox_system.config.get('hub75.disable_hardware_pulsing'),
        },
        'hardware_detection': {
            'pi_model': lightbox_system.config.pi_version,
            'hardware_pwm': lightbox_system.config.has_hardware_pwm,
            'cpu_isolation': lightbox_system.config.has_cpu_isolation,
        }
    })

# =====================================================
# MAIN EXECUTION
# =====================================================

def signal_handler(sig, frame):
    """Handle graceful shutdown."""
    print("\n🛑 Shutting down LightBox system...")
    global lightbox_system
    if lightbox_system:
        lightbox_system.stop_animation()
    sys.exit(0)

def main():
    """Main entry point."""
    global lightbox_system

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🌈 LIGHTBOX HUB75 OPTIMIZED - UNIFIED EDITION")
    print("=" * 50)
    print("Initializing comprehensive HUB75 optimization system...")

    # Initialize system
    lightbox_system = LightBoxSystem()
    if not lightbox_system.initialize():
        print("❌ Failed to initialize LightBox system")
        return 1

    # Start default animation
    if lightbox_system.start_animation('aurora'):
        print("🎬 Started default animation: aurora")
    else:
        print("⚠️  Failed to start default animation")

    # Start web interface
    print("🌐 Starting web interface...")
    print("   📡 Access at: http://localhost:5000")
    print("   🎛️  Full control panel with real-time monitoring")
    print("   📊 Performance metrics and hardware status")
    print("=" * 50)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

    return 0

if __name__ == '__main__':
    sys.exit(main())
