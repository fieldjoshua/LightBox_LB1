"""
WebAPI module for LightBox
Provides Flask routes for web-based control
"""

import os
import logging
import time
import threading
import socket
import platform
import subprocess
from pathlib import Path

# Flask imports
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


def create_app(conductor):
    """Create the Flask application with all routes and SocketIO support."""
    app = Flask(__name__, 
                static_folder=str(Path(__file__).parent.parent / 'web' / 
                                  'static'),
                template_folder=str(Path(__file__).parent.parent / 'web' / 
                                    'templates'))
    
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    
    # Enable CORS if configured
    CORS(app)
    
    # Secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lightbox-dev-key')
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Store reference to conductor
    app.conductor = conductor
    
    # Create performance updater thread
    performance_thread = PerformanceUpdater(socketio, conductor)
    performance_thread.start()
    
    # Home route
    @app.route('/')
    def index():
        print("Index route called")
        return render_template('index.html')
    
    # Comprehensive control panel route
    @app.route('/comprehensive')
    def comprehensive():
        print("Comprehensive route called")
        return render_template('comprehensive.html')
    
    # Static file serving
    @app.route('/static/<path:path>')
    def send_static(path):
        print(f"Static route called for {path}")
        return send_from_directory(app.static_folder, path)
    
    # API Routes
    
    @app.route('/api/status')
    def get_status():
        """Get current system status."""
        try:
            return jsonify({
                "status": "ok",
                "uptime": time.time() - app.conductor.performance.start_time,
                "fps": app.conductor.performance.get_fps(),
                "current_program": app.conductor.config.get("animation_program", ""),
                "programs": list(app.conductor.animations.keys()),
                "brightness": app.conductor.config.get("brightness", 1.0),
                "speed": app.conductor.config.get("animations.speed", 1.0),
                "config": app.conductor.config.get_all()
            })
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/animations')
    def get_animations():
        """Get list of available animations."""
        try:
            animations = list(app.conductor.animations.keys())
            return jsonify({"animations": animations})
        except Exception as e:
            logger.error(f"Error in get_animations: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/animation', methods=['POST'])
    def set_animation():
        """Set current animation."""
        try:
            data = request.get_json()
            if not data or 'animation' not in data:
                return jsonify({"status": "error", "message": "Missing animation parameter"}), 400
            
            animation = data['animation']
            if animation not in app.conductor.animations:
                return jsonify({"status": "error", "message": f"Animation '{animation}' not found"}), 404
            
            success = app.conductor.set_animation(animation)
            if success:
                socketio.emit('status_update', {
                    "current_animation": animation
                })
                return jsonify({"status": "ok"})
            else:
                return jsonify({"status": "error", "message": "Failed to set animation"}), 500
        except Exception as e:
            logger.error(f"Error in set_animation: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/animation/<name>/params')
    def get_animation_params(name):
        """Get parameters for a specific animation."""
        try:
            if name not in app.conductor.animations:
                return jsonify({"status": "error", "message": f"Animation '{name}' not found"}), 404
            
            animation = app.conductor.animations[name]
            params = animation.params if hasattr(animation, 'params') else {}
            
            return jsonify(params)
        except Exception as e:
            logger.error(f"Error in get_animation_params: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/animation/param', methods=['POST'])
    def set_animation_param():
        """Set a parameter for the current animation."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Missing request data"}), 400
                
            animation = data.get('animation')
            param = data.get('param')
            value = data.get('value')
            
            if not animation or not param or value is None:
                return jsonify({"status": "error", "message": "Missing required parameters"}), 400
            
            if animation not in app.conductor.animations:
                return jsonify({"status": "error", "message": f"Animation '{animation}' not found"}), 404
            
            # Update the parameter
            anim_obj = app.conductor.animations[animation]
            if not hasattr(anim_obj, 'params'):
                anim_obj.params = {}
            
            anim_obj.params[param] = value
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in set_animation_param: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/animation/reset', methods=['POST'])
    def reset_animation():
        """Reset the current animation to its default state."""
        try:
            success = app.conductor.reset_animation()
            return jsonify({"status": "ok" if success else "error"})
        except Exception as e:
            logger.error(f"Error in reset_animation: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/brightness', methods=['POST'])
    def set_brightness():
        """Set display brightness."""
        try:
            data = request.get_json()
            if not data or 'brightness' not in data:
                return jsonify({"status": "error", "message": "Missing brightness parameter"}), 400
            
            brightness = float(data['brightness'])
            app.conductor.set_brightness(brightness)
            
            # Send update via WebSocket
            socketio.emit('status_update', {
                "brightness": brightness
            })
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in set_brightness: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/speed', methods=['POST'])
    def set_speed():
        """Set animation speed."""
        try:
            data = request.get_json()
            if not data or 'speed' not in data:
                return jsonify({"status": "error", "message": "Missing speed parameter"}), 400
            
            speed = float(data['speed'])
            app.conductor.set_speed(speed)
            
            # Send update via WebSocket
            socketio.emit('status_update', {
                "speed": speed
            })
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in set_speed: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/palettes')
    def get_palettes():
        """Get available color palettes."""
        try:
            palettes = app.conductor.config.get("palettes", {})
            palette_names = list(palettes.keys())
            if "current" in palette_names:
                palette_names.remove("current")
            
            return jsonify({"palettes": palette_names})
        except Exception as e:
            logger.error(f"Error in get_palettes: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/palette', methods=['POST'])
    def set_palette():
        """Set color palette."""
        try:
            data = request.get_json()
            if not data or 'palette' not in data:
                return jsonify({"status": "error", "message": "Missing palette parameter"}), 400
            
            palette = data['palette']
            app.conductor.set_palette(palette)
            
            # Send update via WebSocket
            socketio.emit('status_update', {
                "palette": palette
            })
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in set_palette: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/presets')
    def get_presets():
        """Get saved presets."""
        try:
            presets = app.conductor.config.get("user_presets", {})
            return jsonify(presets)
        except Exception as e:
            logger.error(f"Error in get_presets: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/preset', methods=['POST'])
    def save_preset():
        """Save current settings as a preset."""
        try:
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({"status": "error", "message": "Missing name parameter"}), 400
            
            name = data['name']
            config_data = data.get('config', {})
            
            # Get current settings if not provided
            if not config_data:
                config_data = {
                    "animation_program": app.conductor.config.get("animation_program"),
                    "brightness": app.conductor.config.get("brightness"),
                    "speed": app.conductor.config.get("animations.speed"),
                    "palette": app.conductor.config.get("palettes.current")
                }
            
            # Save preset
            presets = app.conductor.config.get("user_presets", {})
            presets[name] = config_data
            app.conductor.config.set("user_presets", presets)
            app.conductor.config.save()
            
            return jsonify({"status": "ok", "name": name})
        except Exception as e:
            logger.error(f"Error in save_preset: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/preset/<name>', methods=['GET'])
    def load_preset(name):
        """Load a saved preset."""
        try:
            presets = app.conductor.config.get("user_presets", {})
            if name not in presets:
                return jsonify({"status": "error", "message": f"Preset '{name}' not found"}), 404
            
            preset = presets[name]
            
            # Apply preset settings
            if "animation_program" in preset:
                app.conductor.set_animation(preset["animation_program"])
            
            if "brightness" in preset:
                app.conductor.set_brightness(preset["brightness"])
            
            if "speed" in preset:
                app.conductor.set_speed(preset["speed"])
            
            if "palette" in preset:
                app.conductor.set_palette(preset["palette"])
            
            # Send update via WebSocket
            socketio.emit('status_update', {
                "current_animation": preset.get("animation_program"),
                "brightness": preset.get("brightness"),
                "speed": preset.get("speed"),
                "palette": preset.get("palette")
            })
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in load_preset: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/preset/<name>', methods=['DELETE'])
    def delete_preset(name):
        """Delete a saved preset."""
        try:
            presets = app.conductor.config.get("user_presets", {})
            if name not in presets:
                return jsonify({"status": "error", "message": f"Preset '{name}' not found"}), 404
            
            # Delete preset
            del presets[name]
            app.conductor.config.set("user_presets", presets)
            app.conductor.config.save()
            
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in delete_preset: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/performance')
    def get_performance():
        """Get performance metrics."""
        try:
            metrics = app.conductor.performance.get_metrics()
            return jsonify(metrics)
        except Exception as e:
            logger.error(f"Error in get_performance: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear system caches."""
        try:
            app.conductor.clear_caches()
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in clear_cache: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/emergency-stop', methods=['POST'])
    def emergency_stop():
        """Emergency stop all operations."""
        try:
            app.conductor.emergency_stop()
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Error in emergency_stop: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/hardware/config', methods=['GET', 'POST'])
    def handle_hardware_config():
        """Get or update hardware configuration."""
        if request.method == 'GET':
            try:
                config = app.conductor.config.get_all()
                return jsonify(config)
            except Exception as e:
                logger.error(f"Error getting hardware config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        else:  # POST
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "Missing request data"}), 400
                
                # Update config
                for section, settings in data.items():
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            app.conductor.config.set(f"{section}.{key}", value)
                    else:
                        app.conductor.config.set(section, settings)
                
                # Save config
                app.conductor.config.save()
                
                # Reinitialize hardware if needed
                if 'hub75' in data:
                    # This is a bit dangerous as it might cause flickering or interrupt animations
                    # Ideally, we would signal a clean restart rather than an immediate reinit
                    app.conductor.matrix.initialize()
                
                # Send update via WebSocket
                socketio.emit('config_update', data)
                
                return jsonify({"status": "ok"})
            except Exception as e:
                logger.error(f"Error updating hardware config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/hardware/status', methods=['GET'])
    def get_hardware_status():
        """Get hardware status including PWM detection and CPU isolation."""
        try:
            # Check if matrix driver has detection methods
            hardware_pwm_detected = False
            cpu_isolation_detected = False
            
            if app.conductor.matrix and hasattr(app.conductor.matrix, '_detect_hardware_pwm'):
                hardware_pwm_detected = app.conductor.matrix._detect_hardware_pwm()
            
            if app.conductor.matrix and hasattr(app.conductor.matrix, '_check_cpu_isolation'):
                cpu_isolation_detected = app.conductor.matrix._check_cpu_isolation()
            
            return jsonify({
                "hardware_pwm": hardware_pwm_detected,
                "cpu_isolation": cpu_isolation_detected,
                "matrix_type": app.conductor.config.get("matrix_type", "unknown"),
                "platform": app.conductor.config.get("platform", "unknown")
            })
        except Exception as e:
            logger.error(f"Error getting hardware status: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/system/info', methods=['GET'])
    def get_system_info():
        """Get system information."""
        try:
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
            
            # Get software version
            version = "LightBox v2.0"
            
            # Get driver version
            driver_version = "Unknown"
            if app.conductor.matrix:
                driver_class = app.conductor.matrix.__class__.__name__
                driver_version = driver_class
            
            # Get network status
            ip_address = "Unknown"
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
                s.close()
            except:
                pass
            
            network_status = f"Connected ({ip_address})" if ip_address != "Unknown" else "Disconnected"
            
            return jsonify({
                "pi_model": pi_model,
                "software_version": version,
                "driver_version": driver_version,
                "network_status": network_status
            })
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/system/optimize', methods=['POST'])
    def optimize_system():
        """Apply system-level optimizations for performance."""
        try:
            optimizations = []
            
            # 1. Set CPU governor to performance mode
            if os.path.exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'):
                try:
                    subprocess.run(['sudo', 'cpufreq-set', '-g', 'performance'], 
                                   check=True, capture_output=True)
                    optimizations.append("Set CPU governor to performance mode")
                except:
                    pass
            
            # 2. Apply CPU isolation if enabled
            if app.conductor.config.get("performance.cpu_isolation", False):
                # Check if isolcpus is already in cmdline
                cpu_isolated = False
                try:
                    with open('/proc/cmdline', 'r') as f:
                        cmdline = f.read()
                        if 'isolcpus=3' in cmdline:
                            cpu_isolated = True
                except:
                    pass
                
                if not cpu_isolated:
                    optimizations.append("CPU isolation recommended: Add 'isolcpus=3' to /boot/cmdline.txt and reboot")
            
            # 3. Set minimal GPU memory if not already set
            if os.path.exists('/boot/config.txt'):
                gpu_mem_set = False
                try:
                    with open('/boot/config.txt', 'r') as f:
                        config = f.read()
                        if 'gpu_mem=' in config:
                            gpu_mem_set = True
                except:
                    pass
                
                if not gpu_mem_set:
                    optimizations.append("GPU memory optimization recommended: Add 'gpu_mem=16' to /boot/config.txt")
            
            # 4. Kill unnecessary processes
            try:
                for process in ['lxpanel', 'xscreensaver', 'lightdm']:
                    subprocess.run(['sudo', 'killall', '-q', process], 
                                   stderr=subprocess.DEVNULL)
                optimizations.append("Terminated non-essential GUI processes")
            except:
                pass
            
            # 5. Apply kernel parameters for real-time priority
            try:
                # Set process priority to real-time for the conductor
                subprocess.run(['sudo', 'chrt', '-f', '-p', '99', str(os.getpid())], 
                               check=True, capture_output=True)
                optimizations.append("Set process priority to real-time")
            except:
                pass
            
            # Update config to reflect optimized status
            app.conductor.config.set("system.os_optimization", True)
            app.conductor.config.save()
            
            if not optimizations:
                optimizations.append("System already optimized")
            
            return jsonify({
                "status": "ok",
                "optimizations": optimizations,
                "message": "System optimizations applied"
            })
        except Exception as e:
            logger.error(f"Error optimizing system: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/system/restart', methods=['POST'])
    def restart_system():
        """Restart the LightBox service."""
        try:
            # This is a simple approach - in production you would use a process manager
            threading.Thread(target=restart_application, args=(app.conductor,)).start()
            
            return jsonify({"status": "ok", "message": "System restart initiated"})
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # Optimization API Routes
    
    @app.route('/api/optimization/update', methods=['POST'])
    def update_optimization():
        """Update a single optimization parameter."""
        try:
            data = request.get_json()
            if not data or 'parameter' not in data or 'value' not in data:
                return jsonify({"status": "error", "message": "Missing parameter or value"}), 400
            
            parameter = data['parameter']
            value = data['value']
            
            # Map parameter names to config keys
            param_map = {
                'enable-caching': 'performance.enable_caching',
                'cache-size': 'performance.cache_size',
                'buffer-pool-size': 'performance.buffer_pool_size',
                'adaptive-fps': 'performance.adaptive_fps',
                'frame-skip': 'performance.frame_skip',
                'enable-profiling': 'performance.enable_profiling',
                'complexity': 'complexity',
                'density': 'density',
                'motion-blur': 'effects.motion_blur',
                'fade-rate': 'fade_rate',
                'transition-speed': 'transition_speed',
                'rotation-speed': 'rotation_speed',
                'blur-radius': 'effects.blur_radius',
                'edge-fade': 'effects.edge_fade',
                'center-focus': 'effects.center_focus',
                'vignette': 'effects.vignette',
                'strobe-rate': 'strobe_rate',
                'pulse-speed': 'pulse_speed',
                'gamma': 'gamma',
                'contrast': 'contrast',
                'saturation': 'saturation',
                'hue-shift': 'hue_shift',
                'color-temperature': 'color_temperature',
                'kaleidoscope-segments': 'kaleidoscope_segments',
                'zoom-speed': 'zoom_speed',
                'stats-interval': 'performance.stats_interval'
            }
            
            config_key = param_map.get(parameter, parameter)
            app.conductor.config.set(config_key, value)
            
            # Send update via WebSocket
            socketio.emit('optimization_update', {
                "parameter": parameter,
                "value": value
            })
            
            return jsonify({"status": "ok", "parameter": parameter, "value": value})
        except Exception as e:
            logger.error(f"Error updating optimization: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/optimization/config', methods=['GET', 'POST'])
    def handle_optimization_config():
        """Get or set optimization configuration."""
        try:
            if request.method == 'GET':
                # Return current optimization config
                config = {
                    'enable-caching': app.conductor.config.get('performance.enable_caching', True),
                    'cache-size': app.conductor.config.get('performance.cache_size', 1000),
                    'buffer-pool-size': app.conductor.config.get('performance.buffer_pool_size', 4),
                    'adaptive-fps': app.conductor.config.get('performance.adaptive_fps', True),
                    'frame-skip': app.conductor.config.get('performance.frame_skip', 0),
                    'enable-profiling': app.conductor.config.get('performance.enable_profiling', False),
                    'complexity': app.conductor.config.get('complexity', 5),
                    'density': app.conductor.config.get('density', 0.8),
                    'motion-blur': app.conductor.config.get('effects.motion_blur', 0.2),
                    'fade-rate': app.conductor.config.get('fade_rate', 0.1),
                    'transition-speed': app.conductor.config.get('transition_speed', 1.0),
                    'rotation-speed': app.conductor.config.get('rotation_speed', 0.0),
                    'blur-radius': app.conductor.config.get('effects.blur_radius', 0),
                    'edge-fade': app.conductor.config.get('effects.edge_fade', 0.0),
                    'center-focus': app.conductor.config.get('effects.center_focus', 0.0),
                    'vignette': app.conductor.config.get('effects.vignette', 0.0),
                    'strobe-rate': app.conductor.config.get('strobe_rate', 0),
                    'pulse-speed': app.conductor.config.get('pulse_speed', 1.0),
                    'gamma': app.conductor.config.get('gamma', 2.2),
                    'contrast': app.conductor.config.get('contrast', 1.0),
                    'saturation': app.conductor.config.get('saturation', 1.0),
                    'hue-shift': app.conductor.config.get('hue_shift', 0.0),
                    'color-temperature': app.conductor.config.get('color_temperature', 6500),
                    'kaleidoscope-segments': app.conductor.config.get('kaleidoscope_segments', 6),
                    'zoom-speed': app.conductor.config.get('zoom_speed', 1.0),
                    'stats-interval': app.conductor.config.get('performance.stats_interval', 5)
                }
                return jsonify(config)
            
            else:  # POST
                data = request.get_json()
                if not data:
                    return jsonify({"status": "error", "message": "No configuration provided"}), 400
                
                # Update all optimization parameters
                param_map = {
                    'enable-caching': 'performance.enable_caching',
                    'cache-size': 'performance.cache_size',
                    'buffer-pool-size': 'performance.buffer_pool_size',
                    'adaptive-fps': 'performance.adaptive_fps',
                    'frame-skip': 'performance.frame_skip',
                    'enable-profiling': 'performance.enable_profiling',
                    'complexity': 'complexity',
                    'density': 'density',
                    'motion-blur': 'effects.motion_blur',
                    'fade-rate': 'fade_rate',
                    'transition-speed': 'transition_speed',
                    'rotation-speed': 'rotation_speed',
                    'blur-radius': 'effects.blur_radius',
                    'edge-fade': 'effects.edge_fade',
                    'center-focus': 'effects.center_focus',
                    'vignette': 'effects.vignette',
                    'strobe-rate': 'strobe_rate',
                    'pulse-speed': 'pulse_speed',
                    'gamma': 'gamma',
                    'contrast': 'contrast',
                    'saturation': 'saturation',
                    'hue-shift': 'hue_shift',
                    'color-temperature': 'color_temperature',
                    'kaleidoscope-segments': 'kaleidoscope_segments',
                    'zoom-speed': 'zoom_speed',
                    'stats-interval': 'performance.stats_interval'
                }
                
                for param, value in data.items():
                    config_key = param_map.get(param, param)
                    app.conductor.config.set(config_key, value)
                
                # Send update via WebSocket
                socketio.emit('optimization_config_update', data)
                
                return jsonify({"status": "ok", "config": data})
        except Exception as e:
            logger.error(f"Error handling optimization config: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/optimization/reset', methods=['POST'])
    def reset_optimization():
        """Reset optimization settings to defaults."""
        try:
            defaults = {
                'enable-caching': True,
                'cache-size': 1000,
                'buffer-pool-size': 4,
                'adaptive-fps': True,
                'frame-skip': 0,
                'enable-profiling': False,
                'complexity': 5,
                'density': 0.8,
                'motion-blur': 0.2,
                'fade-rate': 0.1,
                'transition-speed': 1.0,
                'rotation-speed': 0.0,
                'blur-radius': 0,
                'edge-fade': 0.0,
                'center-focus': 0.0,
                'vignette': 0.0,
                'strobe-rate': 0,
                'pulse-speed': 1.0,
                'gamma': 2.2,
                'contrast': 1.0,
                'saturation': 1.0,
                'hue-shift': 0.0,
                'color-temperature': 6500,
                'kaleidoscope-segments': 6,
                'zoom-speed': 1.0,
                'stats-interval': 5
            }
            
            param_map = {
                'enable-caching': 'performance.enable_caching',
                'cache-size': 'performance.cache_size',
                'buffer-pool-size': 'performance.buffer_pool_size',
                'adaptive-fps': 'performance.adaptive_fps',
                'frame-skip': 'performance.frame_skip',
                'enable-profiling': 'performance.enable_profiling',
                'complexity': 'complexity',
                'density': 'density',
                'motion-blur': 'effects.motion_blur',
                'fade-rate': 'fade_rate',
                'transition-speed': 'transition_speed',
                'rotation-speed': 'rotation_speed',
                'blur-radius': 'effects.blur_radius',
                'edge-fade': 'effects.edge_fade',
                'center-focus': 'effects.center_focus',
                'vignette': 'effects.vignette',
                'strobe-rate': 'strobe_rate',
                'pulse-speed': 'pulse_speed',
                'gamma': 'gamma',
                'contrast': 'contrast',
                'saturation': 'saturation',
                'hue-shift': 'hue_shift',
                'color-temperature': 'color_temperature',
                'kaleidoscope-segments': 'kaleidoscope_segments',
                'zoom-speed': 'zoom_speed',
                'stats-interval': 'performance.stats_interval'
            }
            
            for param, value in defaults.items():
                config_key = param_map.get(param, param)
                app.conductor.config.set(config_key, value)
            
            # Send update via WebSocket
            socketio.emit('optimization_reset', defaults)
            
            return jsonify({"status": "ok", "config": defaults})
        except Exception as e:
            logger.error(f"Error resetting optimization: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @app.route('/api/optimization/preset', methods=['POST'])
    def apply_optimization_preset():
        """Apply optimization preset (performance, quality, balanced)."""
        try:
            data = request.get_json()
            if not data or 'preset' not in data:
                return jsonify({"status": "error", "message": "Missing preset parameter"}), 400
            
            preset = data['preset']
            
            # Define preset configurations
            presets = {
                'performance': {
                    'enable-caching': True,
                    'cache-size': 2000,
                    'buffer-pool-size': 6,
                    'adaptive-fps': True,
                    'frame-skip': 1,
                    'enable-profiling': False,
                    'complexity': 3,
                    'density': 0.6,
                    'motion-blur': 0.1,
                    'fade-rate': 0.2,
                    'transition-speed': 2.0,
                    'rotation-speed': 0.0,
                    'blur-radius': 0,
                    'edge-fade': 0.0,
                    'center-focus': 0.0,
                    'vignette': 0.0,
                    'strobe-rate': 0,
                    'pulse-speed': 2.0,
                    'gamma': 2.0,
                    'contrast': 1.2,
                    'saturation': 1.0,
                    'hue-shift': 0.0,
                    'color-temperature': 6500,
                    'kaleidoscope-segments': 4,
                    'zoom-speed': 1.5,
                    'stats-interval': 10
                },
                'quality': {
                    'enable-caching': True,
                    'cache-size': 5000,
                    'buffer-pool-size': 8,
                    'adaptive-fps': False,
                    'frame-skip': 0,
                    'enable-profiling': True,
                    'complexity': 8,
                    'density': 1.0,
                    'motion-blur': 0.4,
                    'fade-rate': 0.05,
                    'transition-speed': 0.5,
                    'rotation-speed': 0.0,
                    'blur-radius': 2,
                    'edge-fade': 0.2,
                    'center-focus': 0.1,
                    'vignette': 0.1,
                    'strobe-rate': 0,
                    'pulse-speed': 0.5,
                    'gamma': 2.4,
                    'contrast': 1.0,
                    'saturation': 1.2,
                    'hue-shift': 0.0,
                    'color-temperature': 6500,
                    'kaleidoscope-segments': 8,
                    'zoom-speed': 0.8,
                    'stats-interval': 2
                },
                'balanced': {
                    'enable-caching': True,
                    'cache-size': 1500,
                    'buffer-pool-size': 4,
                    'adaptive-fps': True,
                    'frame-skip': 0,
                    'enable-profiling': False,
                    'complexity': 5,
                    'density': 0.8,
                    'motion-blur': 0.2,
                    'fade-rate': 0.1,
                    'transition-speed': 1.0,
                    'rotation-speed': 0.0,
                    'blur-radius': 1,
                    'edge-fade': 0.1,
                    'center-focus': 0.05,
                    'vignette': 0.05,
                    'strobe-rate': 0,
                    'pulse-speed': 1.0,
                    'gamma': 2.2,
                    'contrast': 1.0,
                    'saturation': 1.0,
                    'hue-shift': 0.0,
                    'color-temperature': 6500,
                    'kaleidoscope-segments': 6,
                    'zoom-speed': 1.0,
                    'stats-interval': 5
                }
            }
            
            if preset not in presets:
                return jsonify({"status": "error", "message": "Invalid preset"}), 400
            
            config = presets[preset]
            
            # Apply preset configuration
            param_map = {
                'enable-caching': 'performance.enable_caching',
                'cache-size': 'performance.cache_size',
                'buffer-pool-size': 'performance.buffer_pool_size',
                'adaptive-fps': 'performance.adaptive_fps',
                'frame-skip': 'performance.frame_skip',
                'enable-profiling': 'performance.enable_profiling',
                'complexity': 'complexity',
                'density': 'density',
                'motion-blur': 'effects.motion_blur',
                'fade-rate': 'fade_rate',
                'transition-speed': 'transition_speed',
                'rotation-speed': 'rotation_speed',
                'blur-radius': 'effects.blur_radius',
                'edge-fade': 'effects.edge_fade',
                'center-focus': 'effects.center_focus',
                'vignette': 'effects.vignette',
                'strobe-rate': 'strobe_rate',
                'pulse-speed': 'pulse_speed',
                'gamma': 'gamma',
                'contrast': 'contrast',
                'saturation': 'saturation',
                'hue-shift': 'hue_shift',
                'color-temperature': 'color_temperature',
                'kaleidoscope-segments': 'kaleidoscope_segments',
                'zoom-speed': 'zoom_speed',
                'stats-interval': 'performance.stats_interval'
            }
            
            for param, value in config.items():
                config_key = param_map.get(param, param)
                app.conductor.config.set(config_key, value)
            
            # Send update via WebSocket
            socketio.emit('optimization_preset_applied', {
                "preset": preset,
                "config": config
            })
            
            return jsonify({"status": "ok", "preset": preset, "config": config})
        except Exception as e:
            logger.error(f"Error applying optimization preset: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # Socket.IO Events
    
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        # Send initial status
        emit_status_update(socketio, app.conductor)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
    
    return app, socketio

def restart_application(conductor):
    """Clean shutdown and restart the application."""
    # Give time for the response to be sent
    time.sleep(1)
    
    # Stop the conductor
    try:
        conductor.stop()
    except:
        pass
    
    # Restart the process
    try:
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except:
        os.execv(sys.argv[0], sys.argv)

def emit_status_update(socketio, conductor):
    """Emit current status via WebSocket."""
    try:
        status = {
            "current_animation": conductor.config.get("animation_program", ""),
            "brightness": conductor.config.get("brightness", 1.0),
            "speed": conductor.config.get("animations.speed", 1.0),
            "palette": conductor.config.get("palettes.current", "")
        }
        socketio.emit('status_update', status)
    except Exception as e:
        logger.error(f"Error emitting status update: {e}")

class PerformanceUpdater(threading.Thread):
    """Thread to emit performance updates via WebSocket."""
    
    def __init__(self, socketio, conductor, update_interval=1.0):
        super().__init__(daemon=True)
        self.socketio = socketio
        self.conductor = conductor
        self.update_interval = update_interval
        self.running = True
    
    def run(self):
        while self.running:
            try:
                # Get performance metrics
                metrics = self.conductor.performance.get_metrics() if self.conductor.performance else {}
                
                # Add refresh rate if available
                refresh_rate = 0
                if hasattr(self.conductor.matrix, 'refresh_rate'):
                    refresh_rate = self.conductor.matrix.refresh_rate
                
                # Create performance data
                performance_data = {
                    "fps": metrics.get("fps", 0),
                    "frame_count": metrics.get("frame_count", 0),
                    "refresh_rate": refresh_rate,
                    "cpu_usage": metrics.get("cpu_percent", 0),
                    "memory_usage": metrics.get("memory_bytes", 0),
                    "uptime": time.time() - self.conductor.performance.start_time if self.conductor.performance else 0
                }
                
                # Emit update
                self.socketio.emit('performance_update', performance_data)
                
                # Check hardware status periodically (every 10 seconds)
                if int(time.time()) % 10 == 0:
                    self.update_hardware_status()
                
            except Exception as e:
                logger.error(f"Error in performance updater: {e}")
            
            # Sleep
            time.sleep(self.update_interval)
    
    def update_hardware_status(self):
        """Update hardware status information."""
        try:
            # Check if matrix driver has detection methods
            hardware_pwm_detected = False
            cpu_isolation_detected = False
            
            if self.conductor.matrix and hasattr(self.conductor.matrix, '_detect_hardware_pwm'):
                hardware_pwm_detected = self.conductor.matrix._detect_hardware_pwm()
            
            if self.conductor.matrix and hasattr(self.conductor.matrix, '_check_cpu_isolation'):
                cpu_isolation_detected = self.conductor.matrix._check_cpu_isolation()
            
            self.socketio.emit('hardware_status', {
                "hardware_pwm": hardware_pwm_detected,
                "cpu_isolation": cpu_isolation_detected
            })
        except Exception as e:
            logger.error(f"Error updating hardware status: {e}")
    
    def stop(self):
        """Stop the updater thread."""
        self.running = False