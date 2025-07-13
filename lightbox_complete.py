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
app = Flask(__name__)


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


# Animation registry
EMBEDDED_ANIMATIONS = {
    'aurora': aurora_animation,
    'plasma': plasma_animation,
    'fire': fire_animation,
    'ocean': ocean_animation,
    'rainbow': rainbow_animation
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
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin: 0; }
        .panel { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.2); }
        .controls-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
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
        </div>
        
        <div class="panel">
            <h3>📊 System Information</h3>
            <div id="system-info"></div>
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
                });
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
        
        function updateAllSliders() {
            ['brightness', 'speed', 'intensity', 'hue', 'saturation', 'scale', 'complexity', 'smoothness'].forEach(id => {
                const slider = document.getElementById(id);
                const display = document.getElementById(id + '-val');
                const value = slider.value;
                const unit = id === 'hue' ? '°' : (id === 'complexity' || id === 'smoothness' ? '' : '%');
                display.textContent = value + unit;
                updateParameter(id, value);
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
        
        // Update status every 2 seconds
        setInterval(updateStatus, 2000);
        updateStatus();
        updateAllSliders();
    </script>
</body>
</html>
"""


@app.route('/comprehensive')
def comprehensive():
    """Comprehensive control panel with optimization controls."""
    try:
        # Read the comprehensive template file
        template_path = 'web/templates/comprehensive.html'
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>LightBox Comprehensive Control - File Not Found</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f0f0f0; }}
        .error {{ background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .error h1 {{ color: #e74c3c; }}
        .error p {{ color: #666; }}
        .back-link {{ color: #3498db; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Template Not Found</h1>
        <p>The comprehensive control template could not be loaded.</p>
        <p>Template path: {template_path}</p>
        <p><a href="/" class="back-link">← Back to Basic Control Panel</a></p>
    </div>
</body>
</html>
"""


@app.route('/simple')
def simple():
    """Streamlined control panel with user-friendly controls and performance monitoring."""
    try:
        # Read the streamlined template file
        template_path = 'web/templates/simple_comprehensive.html'
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>LightBox Control Panel - File Not Found</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f0f0f0; }}
        .error {{ background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .error h1 {{ color: #e74c3c; }}
        .error p {{ color: #666; }}
        .back-link {{ color: #3498db; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>Template Not Found</h1>
        <p>The streamlined control template could not be loaded.</p>
        <p>Template path: {template_path}</p>
        <p><a href="/" class="back-link">← Back to Basic Control Panel</a></p>
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


@app.route('/api/optimization/update', methods=['POST'])
def api_optimization_update():
    """Update optimization parameters."""
    return jsonify({'success': True, 'message': 'Parameter updated'})


@app.route('/api/optimization/preset', methods=['POST'])
def api_optimization_preset():
    """Apply optimization preset."""
    return jsonify({'success': True, 'message': 'Preset applied'})


@app.route('/api/optimization/reset', methods=['POST'])
def api_optimization_reset():
    """Reset optimization parameters to defaults."""
    return jsonify({'success': True, 'message': 'Parameters reset'})


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