"""
Optimized Flask web interface with caching and performance improvements.
Consolidates the best features from all web implementations.
"""

import os
import json
import time
import threading
import queue
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional

import logging

# Try to import Flask dependencies
try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Flask not available - web interface disabled")

logger = logging.getLogger(__name__)

# Try to import SocketIO for real-time updates
try:
    from flask_socketio import SocketIO, emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("Flask-SocketIO not available - real-time updates disabled")


class ResponseCache:
    """Simple TTL cache for API responses."""
    
    def __init__(self, default_ttl: int = 60):
        self.cache = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self.cache[key] = (value, time.time() + ttl)
    
    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self.cache.clear()


def cached_route(ttl: int = 60):
    """Decorator for caching route responses."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = response_cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Generate response
            response = f(*args, **kwargs)
            
            # Cache response
            response_cache.set(cache_key, response, ttl)
            
            return response
        
        return decorated_function
    return decorator


# Global cache instance
response_cache = ResponseCache()


class UpdateBatcher:
    """Batch WebSocket updates to reduce overhead."""
    
    def __init__(self, batch_interval: float = 0.1):
        self.batch_interval = batch_interval
        self.update_queue = queue.Queue()
        self._running = False
        self._thread = None
    
    def start(self, socketio):
        """Start the batch processor."""
        self._running = True
        self._thread = threading.Thread(
            target=self._process_updates,
            args=(socketio,),
            daemon=True
        )
        self._thread.start()
    
    def stop(self):
        """Stop the batch processor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def add_update(self, event: str, data: Any):
        """Add an update to the queue."""
        try:
            self.update_queue.put((event, data), block=False)
        except queue.Full:
            logger.warning("Update queue full, dropping update")
    
    def _process_updates(self, socketio):
        """Process batched updates."""
        while self._running:
            updates = []
            deadline = time.time() + self.batch_interval
            
            # Collect updates for batch interval
            while time.time() < deadline:
                try:
                    timeout = deadline - time.time()
                    if timeout > 0:
                        update = self.update_queue.get(timeout=timeout)
                        updates.append(update)
                except queue.Empty:
                    break
            
            # Send batched updates
            if updates and socketio:
                try:
                    socketio.emit('batch_update', {
                        'updates': updates,
                        'timestamp': time.time()
                    })
                except Exception as e:
                    logger.error(f"Error sending batch update: {e}")


def create_app(conductor):
    """Create Flask application with conductor integration."""
    if not FLASK_AVAILABLE:
        logger.error("Flask not available - cannot create web app")
        return None
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lightbox-secret-key')
    
    # Enable CORS if configured
    if conductor.config.get("web.enable_cors", False):
        CORS(app)
    
    # Create SocketIO if available
    socketio = None
    update_batcher = UpdateBatcher(
        batch_interval=conductor.config.get("web.update_batch_ms", 100) / 1000
    )
    
    if SOCKETIO_AVAILABLE:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        update_batcher.start(socketio)
    
    # Store references
    app.conductor = conductor
    app.socketio = socketio
    app.update_batcher = update_batcher
    
    # API Routes
    
    @app.route('/')
    def index():
        """Serve the main interface."""
        return render_template('index.html')
    
    @app.route('/comprehensive')
    def comprehensive():
        """Serve the comprehensive parameter interface."""
        return render_template('comprehensive.html')
    
    @app.route('/api/status')
    def get_status():
        """Get current system status."""
        return jsonify(conductor.get_status())
    
    @app.route('/api/config', methods=['GET', 'POST'])
    def handle_config():
        """Get or update configuration."""
        if request.method == 'GET':
            # Return current config
            config_data = {
                'brightness': conductor.config.get('brightness'),
                'speed': conductor.config.get('speed'),
                'animation_program': conductor.config.get('animation_program'),
                'color_palette': conductor.config.get('color_palette'),
                'matrix_type': conductor.config.get('matrix_type'),
                'target_fps': conductor.config.get('target_fps')
            }
            return jsonify(config_data)
        
        else:  # POST
            # Update configuration
            data = request.get_json()
            
            if 'brightness' in data:
                conductor.set_brightness(float(data['brightness']))
            
            if 'speed' in data:
                conductor.set_speed(float(data['speed']))
            
            if 'animation_program' in data:
                conductor.set_animation(data['animation_program'])
            
            if 'color_palette' in data:
                conductor.set_palette(data['color_palette'])
            
            # Clear cache on config change
            response_cache.clear()
            
            # Send update via WebSocket
            if app.socketio:
                update_batcher.add_update('config_update', data)
            
            return jsonify({'status': 'success'})
    
    @app.route('/api/animations')
    @cached_route(ttl=300)  # Cache for 5 minutes
    def get_animations():
        """Get list of available animations."""
        animations = []
        
        for name, anim in conductor.animations.items():
            animations.append({
                'name': name,
                'params': anim.params
            })
        
        return jsonify(animations)
    
    @app.route('/api/programs')
    @cached_route(ttl=300)  # Cache for 5 minutes
    def get_programs():
        """Get list of available animation programs (alias for animations)."""
        # Programs and animations are the same thing in this context
        return get_animations()
    
    @app.route('/api/brightness', methods=['POST'])
    def set_brightness():
        """Set brightness directly."""
        data = request.get_json()
        brightness = float(data.get('brightness', 0.8))
        conductor.set_brightness(brightness)
        
        if app.socketio:
            update_batcher.add_update('brightness', brightness)
        
        return jsonify({'brightness': brightness})
    
    @app.route('/api/speed', methods=['POST'])
    def set_speed():
        """Set animation speed."""
        data = request.get_json()
        speed = float(data.get('speed', 1.0))
        conductor.set_speed(speed)
        
        if app.socketio:
            update_batcher.add_update('speed', speed)
        
        return jsonify({'speed': speed})
    
    @app.route('/api/animation', methods=['POST'])
    def set_animation():
        """Set current animation."""
        data = request.get_json()
        animation = data.get('animation')
        
        if conductor.set_animation(animation):
            if app.socketio:
                update_batcher.add_update('animation', animation)
            return jsonify({'animation': animation})
        else:
            return jsonify({'error': 'Animation not found'}), 404
    
    @app.route('/api/palettes')
    @cached_route(ttl=300)
    def get_palettes():
        """Get available color palettes."""
        palettes = ['rainbow', 'fire', 'ocean', 'forest']
        return jsonify(palettes)
    
    @app.route('/api/palette', methods=['POST'])
    def set_palette():
        """Set color palette."""
        data = request.get_json()
        palette = data.get('palette')
        conductor.set_palette(palette)
        
        if app.socketio:
            update_batcher.add_update('palette', palette)
        
        return jsonify({'palette': palette})
    
    @app.route('/api/presets')
    def get_presets():
        """Get list of saved presets."""
        preset_dir = Path("presets")
        presets = []
        
        if preset_dir.exists():
            for preset_file in preset_dir.glob("*.json"):
                presets.append(preset_file.stem)
        
        return jsonify(presets)
    
    @app.route('/api/preset/<name>', methods=['GET', 'POST', 'DELETE'])
    def handle_preset(name):
        """Load, save, or delete a preset."""
        if request.method == 'GET':
            # Load preset
            if conductor.load_preset(name):
                return jsonify({'status': 'loaded'})
            else:
                return jsonify({'error': 'Preset not found'}), 404
        
        elif request.method == 'POST':
            # Save preset
            conductor.save_preset(name)
            return jsonify({'status': 'saved'})
        
        else:  # DELETE
            # Delete preset
            preset_path = Path("presets") / f"{name}.json"
            if preset_path.exists():
                preset_path.unlink()
                return jsonify({'status': 'deleted'})
            else:
                return jsonify({'error': 'Preset not found'}), 404
    
    @app.route('/api/performance')
    def get_performance():
        """Get performance metrics."""
        return jsonify(conductor.performance.get_stats())
    
    @app.route('/api/animation/param', methods=['POST'])
    def set_animation_param():
        """Set animation parameter."""
        data = request.get_json()
        param = data.get('param')
        value = data.get('value')
        
        if conductor.set_animation_param(param, value):
            if app.socketio:
                update_batcher.add_update('animation_param', {'param': param, 'value': value})
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to set parameter'}), 400
    
    @app.route('/api/animation/reset', methods=['POST'])
    def reset_animation():
        """Reset current animation."""
        if conductor.reset_animation():
            if app.socketio:
                update_batcher.add_update('animation_reset', {})
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to reset animation'}), 400
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear all caches."""
        conductor.clear_caches()
        response_cache.clear()
        
        if app.socketio:
            update_batcher.add_update('cache_cleared', {})
        
        return jsonify({'status': 'success'})
    
    @app.route('/api/emergency-stop', methods=['POST'])
    def emergency_stop():
        """Emergency stop - halt all animations immediately."""
        conductor.emergency_stop()
        
        if app.socketio:
            update_batcher.add_update('emergency_stop', {})
        
        return jsonify({'status': 'stopped'})
    
    @app.route('/api/hardware/config', methods=['GET', 'POST'])
    def handle_hardware_config():
        """Get or update hardware configuration."""
        if request.method == 'GET':
            # Return current hardware config
            hw_config = {
                'ws2811': conductor.config.get('ws2811', {}),
                'hub75': conductor.config.get('hub75', {}),
                'performance': conductor.config.get('performance', {}),
                'platform': conductor.config.get('platform', {})
            }
            return jsonify(hw_config)
        
        else:  # POST
            # Update hardware configuration
            data = request.get_json()
            
            for section, config in data.items():
                if section in ['ws2811', 'hub75', 'performance', 'platform']:
                    conductor.config.update_section(section, config)
            
            # Clear cache on hardware config change
            response_cache.clear()
            
            # Send update via WebSocket
            if app.socketio:
                update_batcher.add_update('hardware_config_update', data)
            
            return jsonify({'status': 'success'})
    
    @app.route('/api/system/optimize', methods=['POST'])
    def optimize_system():
        """Apply system optimizations."""
        data = request.get_json()
        optimization_type = data.get('type', 'all')
        
        try:
            if optimization_type == 'performance':
                conductor.apply_performance_optimizations()
            elif optimization_type == 'platform':
                conductor.apply_platform_optimizations()
            elif optimization_type == 'cache':
                conductor.rebuild_caches()
            else:  # 'all'
                conductor.apply_all_optimizations()
            
            return jsonify({'status': 'optimizations_applied'})
        except Exception as e:
            logger.error(f"Error applying optimizations: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Static file serving
    @app.route('/static/<path:path>')
    def send_static(path):
        """Serve static files."""
        return send_from_directory('static', path)
    
    # WebSocket events (if available)
    if socketio:
        @socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info("Client connected")
            emit('connected', {'status': 'connected'})
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info("Client disconnected")
        
        @socketio.on('request_update')
        def handle_update_request():
            """Handle request for immediate update."""
            emit('status_update', conductor.get_status())
    
    # Cleanup handler
    def cleanup():
        """Clean up resources."""
        update_batcher.stop()
        response_cache.clear()
    
    app.cleanup = cleanup
    
    return app


def run_server(app, host='0.0.0.0', port=5001, production=False):
    """Run the web server."""
    if app is None:
        logger.error("No app to run - Flask may not be available")
        return
        
    if production and SOCKETIO_AVAILABLE and app.socketio:
        # Use production WSGI server
        try:
            from eventlet import wsgi
            import eventlet
            
            logger.info(f"Starting production server on {host}:{port}")
            wsgi.server(eventlet.listen((host, port)), app)
        except ImportError:
            logger.warning("Eventlet not available, falling back to development server")
            production = False
    
    if not production:
        # Development server
        logger.info(f"Starting development server on {host}:{port}")
        
        if hasattr(app, 'socketio') and app.socketio:
            app.socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
        else:
            app.run(host=host, port=port, debug=False)


# Export main components
__all__ = ['create_app', 'run_server']