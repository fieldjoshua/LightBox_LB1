#!/usr/bin/env python3
"""
Simple LightBox - Clean LED Matrix Controller
A working version built from scratch
"""

import time
import threading
import logging
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMatrix:
    """Simple matrix simulation for development"""
    
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
            self.pixels[idx] = (int(r * self.brightness), 
                               int(g * self.brightness), 
                               int(b * self.brightness))
    
    def clear(self):
        """Clear all pixels"""
        self.pixels = [(0, 0, 0)] * (self.width * self.height)
    
    def show(self):
        """Update display (simulated)"""
        pass
    
    def set_brightness(self, brightness):
        """Set brightness (0.0 to 1.0)"""
        self.brightness = max(0.0, min(1.0, brightness))

class SimpleAnimation:
    """Simple animation base class"""
    
    def __init__(self, name, matrix):
        self.name = name
        self.matrix = matrix
        self.frame = 0
    
    def animate(self):
        """Override this method in subclasses"""
        pass

class RainbowWave(SimpleAnimation):
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

class FireAnimation(SimpleAnimation):
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

class SimpleLightBox:
    """Simple LightBox controller"""
    
    def __init__(self):
        self.matrix = SimpleMatrix(64, 64)
        self.animations = {
            'rainbow': RainbowWave('rainbow', self.matrix),
            'fire': FireAnimation('fire', self.matrix)
        }
        self.current_animation = 'rainbow'
        self.running = False
        self.brightness = 1.0
        self.speed = 1.0
        
        # Web server
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web routes"""
        
        @self.app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Simple LightBox</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .control { margin: 10px 0; }
                    button { padding: 10px 20px; margin: 5px; }
                    .status { padding: 10px; background: #f0f0f0; margin: 10px 0; }
                </style>
            </head>
            <body>
                <h1>🎨 Simple LightBox Controller</h1>
                
                <div class="control">
                    <h3>Animation</h3>
                    <button onclick="setAnimation('rainbow')">Rainbow Wave</button>
                    <button onclick="setAnimation('fire')">Fire</button>
                </div>
                
                <div class="control">
                    <h3>Brightness</h3>
                    <input type="range" id="brightness" min="0" max="100" value="100" 
                           onchange="setBrightness(this.value)">
                    <span id="brightnessValue">100%</span>
                </div>
                
                <div class="control">
                    <h3>Speed</h3>
                    <input type="range" id="speed" min="1" max="10" value="5" 
                           onchange="setSpeed(this.value)">
                    <span id="speedValue">5x</span>
                </div>
                
                <div class="control">
                    <button onclick="start()">Start</button>
                    <button onclick="stop()">Stop</button>
                    <button onclick="clear()">Clear</button>
                </div>
                
                <div class="status" id="status">Status: Ready</div>
                
                <script src="/socket.io/socket.io.js"></script>
                <script>
                    const socket = io();
                    
                    function setAnimation(name) {
                        socket.emit('set_animation', {animation: name});
                        updateStatus('Animation: ' + name);
                    }
                    
                    function setBrightness(value) {
                        socket.emit('set_brightness', {brightness: value / 100});
                        document.getElementById('brightnessValue').textContent = value + '%';
                    }
                    
                    function setSpeed(value) {
                        socket.emit('set_speed', {speed: value});
                        document.getElementById('speedValue').textContent = value + 'x';
                    }
                    
                    function start() {
                        socket.emit('start');
                        updateStatus('Running');
                    }
                    
                    function stop() {
                        socket.emit('stop');
                        updateStatus('Stopped');
                    }
                    
                    function clear() {
                        socket.emit('clear');
                        updateStatus('Cleared');
                    }
                    
                    function updateStatus(message) {
                        document.getElementById('status').textContent = 'Status: ' + message;
                    }
                    
                    socket.on('status', function(data) {
                        updateStatus(data.message);
                    });
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
        """Start the LightBox system"""
        logger.info("Starting Simple LightBox...")
        
        # Start animation loop in background
        animation_thread = threading.Thread(target=self.run_animation_loop, daemon=True)
        animation_thread.start()
        
        # Start web server
        logger.info("Starting web server on http://0.0.0.0:5000")
        self.socketio.run(self.app, host='0.0.0.0', port=5000, 
                         allow_unsafe_werkzeug=True)

def main():
    """Main entry point"""
    print("🎨 Simple LightBox - Clean LED Matrix Controller")
    print("=" * 50)
    
    lightbox = SimpleLightBox()
    lightbox.start()

if __name__ == "__main__":
    main() 