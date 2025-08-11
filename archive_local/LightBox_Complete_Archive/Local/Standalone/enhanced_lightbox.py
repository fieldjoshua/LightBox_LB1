#!/usr/bin/env python3
"""
Enhanced LightBox - LED Matrix Controller with HUB75 Drivers
Uses proper hardware drivers and runs on port 8080
"""

import time
import threading
import logging
import math
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the proper drivers
try:
    from drivers.hub75_driver import HUB75Driver
    HARDWARE_AVAILABLE = True
    logger.info("Hardware drivers available")
except ImportError as e:
    HARDWARE_AVAILABLE = False
    logger.warning(f"Hardware drivers not available: {e}")


class SimulatedMatrix:
    """Simulated matrix for development when hardware not available"""
    
    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height
        self.pixels = [(0, 0, 0)] * (width * height)
        self.brightness = 1.0
        logger.info(f"Initialized simulated matrix: {width}x{height}")
    
    def set_pixel(self, x, y, r, g, b):
        """Set a pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            self.pixels[idx] = (
                int(r * self.brightness),
                int(g * self.brightness),
                int(b * self.brightness)
            )
    
    def clear(self):
        """Clear all pixels"""
        self.pixels = [(0, 0, 0)] * (self.width * self.height)
    
    def show(self):
        """Update display (simulated)"""
        pass
    
    def set_brightness(self, brightness):
        """Set brightness (0.0 to 1.0)"""
        self.brightness = max(0.0, min(1.0, brightness))
    
    def initialize(self):
        """Initialize the matrix"""
        return True

class Animation:
    """Base animation class"""
    
    def __init__(self, name, matrix):
        self.name = name
        self.matrix = matrix
        self.frame = 0
    
    def animate(self):
        """Override this method in subclasses"""
        pass

class RainbowWave(Animation):
    """Rainbow wave animation"""
    
    def animate(self):
        self.frame += 1
        for y in range(self.matrix.height):
            for x in range(self.matrix.width):
                # Create rainbow wave effect
                hue = (x + y + self.frame * 0.1) % 360
                r, g, b = self.hsv_to_rgb(hue, 1.0, 1.0)
                self.matrix.set_pixel(x, y, r, g, b)
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        h = h / 60
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        if i == 0: return (v * 255, t * 255, p * 255)
        elif i == 1: return (q * 255, v * 255, p * 255)
        elif i == 2: return (p * 255, v * 255, t * 255)
        elif i == 3: return (p * 255, q * 255, v * 255)
        elif i == 4: return (t * 255, p * 255, v * 255)
        else: return (v * 255, p * 255, q * 255)

class FireAnimation(Animation):
    """Fire animation"""
    
    def animate(self):
        self.frame += 1
        for y in range(self.matrix.height):
            for x in range(self.matrix.width):
                # Create fire effect
                intensity = (y / self.matrix.height) * 0.8 + 0.2
                flicker = 0.8 + 0.2 * (self.frame % 10) / 10
                r = int(255 * intensity * flicker)
                g = int(128 * intensity * flicker)
                b = int(64 * intensity * flicker)
                self.matrix.set_pixel(x, y, r, g, b)

class PlasmaAnimation(Animation):
    """Plasma animation"""
    
    def animate(self):
        self.frame += 1
        for y in range(self.matrix.height):
            for x in range(self.matrix.width):
                # Create plasma effect
                dx = x - self.matrix.width / 2
                dy = y - self.matrix.height / 2
                angle = (self.frame * 0.02) % (2 * 3.14159)
                
                # Multiple sine waves for plasma effect
                plasma = (math.sin(dx * 0.1 + self.frame * 0.01) +
                         math.sin(dy * 0.1 + self.frame * 0.01) +
                         math.sin((dx + dy) * 0.1 + self.frame * 0.01) +
                         math.sin(math.sqrt(dx*dx + dy*dy) * 0.1 + self.frame * 0.01)) / 4
                
                # Convert to color
                hue = (plasma + 1) * 180  # 0-360
                r, g, b = self.hsv_to_rgb(hue, 1.0, 1.0)
                self.matrix.set_pixel(x, y, r, g, b)
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        h = h / 60
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        if i == 0: return (v * 255, t * 255, p * 255)
        elif i == 1: return (q * 255, v * 255, p * 255)
        elif i == 2: return (p * 255, v * 255, t * 255)
        elif i == 3: return (p * 255, q * 255, v * 255)
        elif i == 4: return (t * 255, p * 255, v * 255)
        else: return (v * 255, p * 255, q * 255)

class EnhancedLightBox:
    """Enhanced LightBox controller with hardware support"""
    
    def __init__(self):
        # Initialize matrix (hardware or simulated)
        if HARDWARE_AVAILABLE:
            try:
                # Try to use HUB75 hardware
                config = {
                    "hub75": {
                        "cols": 64,
                        "rows": 64,
                        "chain_length": 1,
                        "parallel": 1,
                        "gpio_slowdown": 4,
                        "pwm_bits": 11,
                        "pwm_lsb_nanoseconds": 130
                    },
                    "brightness": 0.8,
                    "performance": {
                        "show_refresh_rate": True
                    }
                }
                self.matrix = HUB75Driver(config)
                if self.matrix.initialize():
                    logger.info("✅ HUB75 hardware initialized successfully!")
                    self.hardware_mode = True
                else:
                    logger.warning("⚠️ HUB75 initialization failed, using simulation")
                    self.matrix = SimulatedMatrix(64, 64)
                    self.hardware_mode = False
            except Exception as e:
                logger.error(f"❌ Hardware initialization error: {e}")
                self.matrix = SimulatedMatrix(64, 64)
                self.hardware_mode = False
        else:
            logger.info("🔧 Using simulated matrix (no hardware drivers)")
            self.matrix = SimulatedMatrix(64, 64)
            self.hardware_mode = False
        
        # Initialize animations
        self.animations = {
            'rainbow': RainbowWave('rainbow', self.matrix),
            'fire': FireAnimation('fire', self.matrix),
            'plasma': PlasmaAnimation('plasma', self.matrix)
        }
        self.current_animation = 'rainbow'
        self.running = False
        self.brightness = 1.0
        self.speed = 1.0
        
        # Web server
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web routes"""
        
        @self.app.route('/')
        def index():
            hardware_status = "✅ Hardware" if self.hardware_mode else "🔧 Simulation"
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Enhanced LightBox</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
                    .header {{ background: #333; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                    .control {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                    button {{ padding: 12px 24px; margin: 5px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }}
                    button:hover {{ background: #45a049; }}
                    .status {{ padding: 15px; background: #333; margin: 10px 0; border-radius: 8px; }}
                    input[type="range"] {{ width: 200px; }}
                    .hardware-status {{ color: #4CAF50; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎨 Enhanced LightBox Controller</h1>
                    <p class="hardware-status">Mode: {hardware_status}</p>
                </div>
                
                <div class="control">
                    <h3>🎭 Animation</h3>
                    <button onclick="setAnimation('rainbow')">Rainbow Wave</button>
                    <button onclick="setAnimation('fire')">Fire</button>
                    <button onclick="setAnimation('plasma')">Plasma</button>
                </div>
                
                <div class="control">
                    <h3>💡 Brightness</h3>
                    <input type="range" id="brightness" min="0" max="100" value="100" 
                           onchange="setBrightness(this.value)">
                    <span id="brightnessValue">100%</span>
                </div>
                
                <div class="control">
                    <h3>⚡ Speed</h3>
                    <input type="range" id="speed" min="1" max="10" value="5" 
                           onchange="setSpeed(this.value)">
                    <span id="speedValue">5x</span>
                </div>
                
                <div class="control">
                    <button onclick="start()">▶️ Start</button>
                    <button onclick="stop()">⏹️ Stop</button>
                    <button onclick="clear()">🧹 Clear</button>
                </div>
                
                <div class="status" id="status">Status: Ready</div>
                
                <script src="/socket.io/socket.io.js"></script>
                <script>
                    const socket = io();
                    
                    function setAnimation(name) {{
                        socket.emit('set_animation', {{animation: name}});
                        updateStatus('Animation: ' + name);
                    }}
                    
                    function setBrightness(value) {{
                        socket.emit('set_brightness', {{brightness: value / 100}});
                        document.getElementById('brightnessValue').textContent = value + '%';
                    }}
                    
                    function setSpeed(value) {{
                        socket.emit('set_speed', {{speed: value}});
                        document.getElementById('speedValue').textContent = value + 'x';
                    }}
                    
                    function start() {{
                        socket.emit('start');
                        updateStatus('Running');
                    }}
                    
                    function stop() {{
                        socket.emit('stop');
                        updateStatus('Stopped');
                    }}
                    
                    function clear() {{
                        socket.emit('clear');
                        updateStatus('Cleared');
                    }}
                    
                    function updateStatus(message) {{
                        document.getElementById('status').textContent = 'Status: ' + message;
                    }}
                    
                    socket.on('status', function(data) {{
                        updateStatus(data.message);
                    }});
                </script>
            </body>
            </html>
            '''
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            emit('status', {'message': 'Connected'})
        
        @self.socketio.on('set_animation')
        def handle_set_animation(data):
            animation = data.get('animation', 'rainbow')
            if animation in self.animations:
                self.current_animation = animation
                logger.info(f"Animation changed to: {animation}")
                emit('status', {'message': f'Animation: {animation}'})
        
        @self.socketio.on('set_brightness')
        def handle_set_brightness(data):
            brightness = data.get('brightness', 1.0)
            self.brightness = max(0.0, min(1.0, brightness))
            self.matrix.set_brightness(self.brightness)
            logger.info(f"Brightness set to: {self.brightness}")
        
        @self.socketio.on('set_speed')
        def handle_set_speed(data):
            speed = data.get('speed', 1.0)
            self.speed = max(0.1, min(10.0, speed))
            logger.info(f"Speed set to: {self.speed}")
        
        @self.socketio.on('start')
        def handle_start():
            self.running = True
            logger.info("Animation started")
            emit('status', {'message': 'Running'})
        
        @self.socketio.on('stop')
        def handle_stop():
            self.running = False
            logger.info("Animation stopped")
            emit('status', {'message': 'Stopped'})
        
        @self.socketio.on('clear')
        def handle_clear():
            self.matrix.clear()
            logger.info("Matrix cleared")
            emit('status', {'message': 'Cleared'})
    
    def run_animation_loop(self):
        """Run the animation loop"""
        while True:
            if self.running and self.current_animation in self.animations:
                animation = self.animations[self.current_animation]
                animation.animate()
                self.matrix.show()
            
            time.sleep(0.05 / self.speed)  # 20 FPS base
    
    def start(self):
        """Start the Enhanced LightBox system"""
        logger.info("Starting Enhanced LightBox...")
        
        # Start animation loop in background
        animation_thread = threading.Thread(target=self.run_animation_loop, daemon=True)
        animation_thread.start()
        
        # Start web server on port 8080
        logger.info("Starting web server on http://0.0.0.0:8080")
        self.socketio.run(self.app, host='0.0.0.0', port=8080, 
                         allow_unsafe_werkzeug=True)

def main():
    """Main entry point"""
    print("🎨 Enhanced LightBox - LED Matrix Controller")
    print("=" * 50)
    
    lightbox = EnhancedLightBox()
    lightbox.start()

if __name__ == "__main__":
    main() 