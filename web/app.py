"""
Flask web application for LED matrix control panel
Provides real-time control and monitoring interface
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import os
import sys
import io
import threading
import queue
import time
import importlib.util
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'scripts'
ALLOWED_EXTENSIONS = {'py'}
ALLOWED_FILE_TYPES = {'py', 'txt', 'json', 'md'}

# Terminal output capture
terminal_output = queue.Queue()
terminal_lock = threading.Lock()

class TerminalCapture:
    """Capture terminal output for real-time monitoring"""
    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.buffer = io.StringIO()
        
    def write(self, text):
        self.stdout.write(text)
        self.buffer.write(text)
        with terminal_lock:
            try:
                terminal_output.put_nowait({
                    'timestamp': time.time(),
                    'type': 'stdout',
                    'content': text
                })
            except queue.Full:
                pass
                
    def flush(self):
        self.stdout.flush()

def allowed_file(filename, file_types=None):
    if file_types is None:
        file_types = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in file_types

def get_program_parameters(program_path):
    """Extract configurable parameters from a program file"""
    try:
        with open(program_path, 'r') as f:
            content = f.read()
        
        # Look for parameter definitions in comments
        parameters = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('# PARAM:'):
                # Format: # PARAM: name|type|default|min|max|description
                param_def = line[8:].strip()
                parts = param_def.split('|')
                if len(parts) >= 4:
                    name, param_type, default, description = parts[0], parts[1], parts[2], parts[3]
                    param_min = parts[4] if len(parts) > 4 else None
                    param_max = parts[5] if len(parts) > 5 else None
                    
                    parameters[name] = {
                        'type': param_type,
                        'default': default,
                        'min': param_min,
                        'max': param_max,
                        'description': description
                    }
        
        return parameters
    except Exception as e:
        print(f"Error extracting parameters from {program_path}: {e}")
        return {}

def create_app(led_controller=None):
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['SECRET_KEY'] = 'lightbox_secret_key'
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store LED controller reference
    app.led_controller = led_controller
    app.socketio = socketio
    
    # Store program parameters
    app.program_parameters = {}
    
    @app.route('/')
    def index():
        """Main control panel page"""
        return render_template('enhanced.html')
    
    @app.route('/basic')
    def basic():
        """Basic control panel page"""
        return render_template('index.html')
    
    @app.route('/api/status')
    def get_status():
        """Get current LED system status"""
        if app.led_controller:
            return jsonify({
                'running': app.led_controller.running,
                'current_program': app.led_controller.current_program,
                'config': app.led_controller.config.to_dict(),
                'programs': list(app.led_controller.programs.keys()),
                'stats': app.led_controller.stats
            })
        return jsonify({'error': 'LED controller not initialized'}), 503
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        """Update LED configuration"""
        if not app.led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 503
        
        try:
            data = request.json
            
            # Update configuration
            app.led_controller.update_config(data)
            
            # Save to settings file
            app.led_controller.config.save_settings()
            
            return jsonify({'success': True, 'config': app.led_controller.config.to_dict()})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/program', methods=['POST'])
    def switch_program():
        """Switch animation program"""
        if not app.led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 503
        
        try:
            data = request.json
            program_name = data.get('program')
            
            if app.led_controller.switch_program(program_name):
                return jsonify({
                    'success': True, 
                    'current_program': app.led_controller.current_program
                })
            else:
                return jsonify({'error': 'Invalid program name'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/upload', methods=['POST'])
    def upload_program():
        """Upload new animation program"""
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Ensure scripts directory exists
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
            os.makedirs(scripts_dir, exist_ok=True)
            
            filepath = os.path.join(scripts_dir, filename)
            
            try:
                # Validate Python syntax before saving
                content = file.read()
                compile(content, filename, 'exec')
                
                # Save file
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                # Reload programs if controller exists
                if app.led_controller:
                    app.led_controller.load_programs()
                
                return jsonify({
                    'success': True, 
                    'filename': filename,
                    'message': 'Program uploaded successfully'
                })
            except SyntaxError as e:
                return jsonify({'error': f'Invalid Python syntax: {e}'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Invalid file type. Only .py files allowed'}), 400
    
    @app.route('/api/upload-files', methods=['POST'])
    def upload_files():
        """Upload multiple files to Pi"""
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        upload_type = request.form.get('type', 'scripts')  # scripts, presets, config
        
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename, ALLOWED_FILE_TYPES):
                filename = secure_filename(file.filename)
                
                # Determine upload directory
                if upload_type == 'presets':
                    upload_dir = 'presets'
                elif upload_type == 'config':
                    upload_dir = 'config'
                else:
                    upload_dir = 'scripts'
                
                # Ensure upload directory exists
                upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), upload_dir)
                os.makedirs(upload_path, exist_ok=True)
                
                filepath = os.path.join(upload_path, filename)
                
                try:
                    # Validate Python files
                    content = file.read()
                    if filename.endswith('.py'):
                        compile(content, filename, 'exec')
                    
                    # Save file
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'path': upload_dir
                    })
                    
                except SyntaxError as e:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': f'Invalid Python syntax: {e}'
                    })
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': 'Invalid file type'
                })
        
        # Reload programs if any Python files were uploaded to scripts
        if any(r['status'] == 'success' and r['path'] == 'scripts' for r in results):
            if app.led_controller:
                app.led_controller.load_programs()
                app.program_parameters = {}  # Reset parameters cache
        
        return jsonify({'results': results})
    
    @app.route('/api/program-parameters/<program_name>')
    def get_program_parameters(program_name):
        """Get configurable parameters for a specific program"""
        if program_name not in app.program_parameters:
            # Load parameters from file
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts')
            program_path = os.path.join(scripts_dir, f"{program_name}.py")
            
            if os.path.exists(program_path):
                app.program_parameters[program_name] = get_program_parameters(program_path)
            else:
                app.program_parameters[program_name] = {}
        
        return jsonify({
            'program': program_name,
            'parameters': app.program_parameters[program_name]
        })
    
    @app.route('/api/program-parameters/<program_name>', methods=['POST'])
    def update_program_parameters(program_name):
        """Update parameters for a specific program"""
        try:
            data = request.json
            
            # Store parameters in memory (you might want to persist these)
            if program_name not in app.program_parameters:
                app.program_parameters[program_name] = {}
            
            # Update parameter values
            for param_name, value in data.items():
                if param_name in app.program_parameters[program_name]:
                    app.program_parameters[program_name][param_name]['value'] = value
            
            return jsonify({'success': True, 'parameters': app.program_parameters[program_name]})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/files')
    def list_files():
        """List files on the Pi"""
        try:
            base_path = os.path.dirname(os.path.dirname(__file__))
            files = {}
            
            # List different directories
            directories = ['scripts', 'presets', 'config']
            
            for directory in directories:
                dir_path = os.path.join(base_path, directory)
                files[directory] = []
                
                if os.path.exists(dir_path):
                    for filename in os.listdir(dir_path):
                        if not filename.startswith('.'):
                            file_path = os.path.join(dir_path, filename)
                            stat = os.stat(file_path)
                            files[directory].append({
                                'name': filename,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'type': 'file' if os.path.isfile(file_path) else 'directory'
                            })
            
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/files/<path:filepath>', methods=['DELETE'])
    def delete_file(filepath):
        """Delete a file from the Pi"""
        try:
            base_path = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(base_path, filepath)
            
            # Security check - ensure file is within allowed directories
            allowed_dirs = ['scripts', 'presets', 'config']
            if not any(filepath.startswith(d + '/') for d in allowed_dirs):
                return jsonify({'error': 'Access denied'}), 403
            
            if os.path.exists(full_path):
                os.remove(full_path)
                
                # Reload programs if a script was deleted
                if filepath.startswith('scripts/'):
                    if app.led_controller:
                        app.led_controller.load_programs()
                
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/files/<path:filepath>')
    def download_file(filepath):
        """Download a file from the Pi"""
        try:
            base_path = os.path.dirname(os.path.dirname(__file__))
            full_path = os.path.join(base_path, filepath)
            
            # Security check
            allowed_dirs = ['scripts', 'presets', 'config']
            if not any(filepath.startswith(d + '/') for d in allowed_dirs):
                return jsonify({'error': 'Access denied'}), 403
            
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                
                return jsonify({
                    'filename': os.path.basename(filepath),
                    'content': content,
                    'path': filepath
                })
            else:
                return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats')
    def get_stats():
        """Get runtime statistics"""
        try:
            if os.path.exists('/tmp/cosmic_stats.json'):
                with open('/tmp/cosmic_stats.json', 'r') as f:
                    stats = json.load(f)
                return jsonify(stats)
            return jsonify({'error': 'Stats not available'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/palettes')
    def get_palettes():
        """Get available color palettes"""
        if app.led_controller:
            return jsonify({
                'palettes': list(app.led_controller.config.PALETTES.keys()),
                'current': app.led_controller.config.CURRENT_PALETTE
            })
        return jsonify({'error': 'LED controller not initialized'}), 503
    
    @app.route('/api/palette', methods=['POST'])
    def set_palette():
        """Set active color palette"""
        if not app.led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 503
        
        try:
            data = request.json
            palette_name = data.get('palette')
            
            if palette_name in app.led_controller.config.PALETTES:
                app.led_controller.config.CURRENT_PALETTE = palette_name
                app.led_controller.config.save_settings()
                return jsonify({'success': True, 'palette': palette_name})
            else:
                return jsonify({'error': 'Invalid palette name'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/save-preset', methods=['POST'])
    def save_preset():
        """Save current settings as preset"""
        if not app.led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 503
        
        try:
            data = request.json
            preset_name = data.get('name', 'default')
            
            # Create presets directory
            presets_dir = 'presets'
            os.makedirs(presets_dir, exist_ok=True)
            
            # Save preset
            preset_file = os.path.join(presets_dir, f"{preset_name}.json")
            preset_data = app.led_controller.config.to_dict()
            preset_data['name'] = preset_name
            
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            return jsonify({'success': True, 'preset': preset_name})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/load-preset', methods=['POST'])
    def load_preset():
        """Load settings from preset"""
        if not app.led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 503
        
        try:
            data = request.json
            preset_name = data.get('name', 'default')
            
            preset_file = os.path.join('presets', f"{preset_name}.json")
            
            if os.path.exists(preset_file):
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                
                # Apply preset settings
                app.led_controller.update_config(preset_data)
                app.led_controller.config.save_settings()
                
                return jsonify({'success': True, 'preset': preset_data})
            else:
                return jsonify({'error': 'Preset not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/presets')
    def list_presets():
        """List available presets"""
        try:
            presets_dir = 'presets'
            presets = []
            
            if os.path.exists(presets_dir):
                for filename in os.listdir(presets_dir):
                    if filename.endswith('.json'):
                        preset_name = filename[:-5]
                        presets.append(preset_name)
            
            return jsonify({'presets': presets})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # SocketIO handlers for real-time features
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        emit('connected', {'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('request_terminal_output')
    def handle_terminal_request():
        """Send recent terminal output to client"""
        try:
            output_list = []
            while not terminal_output.empty():
                try:
                    output_list.append(terminal_output.get_nowait())
                except queue.Empty:
                    break
            
            if output_list:
                emit('terminal_output', {'data': output_list})
        except Exception as e:
            emit('error', {'message': str(e)})
    
    @socketio.on('subscribe_terminal')
    def handle_terminal_subscription():
        """Subscribe client to terminal output"""
        emit('terminal_subscribed', {'status': 'subscribed'})
    
    # Terminal output streaming thread
    def terminal_streamer():
        """Stream terminal output to connected clients"""
        while True:
            try:
                if not terminal_output.empty():
                    output_list = []
                    while not terminal_output.empty():
                        try:
                            output_list.append(terminal_output.get_nowait())
                        except queue.Empty:
                            break
                    
                    if output_list:
                        socketio.emit('terminal_output', {'data': output_list})
                
                time.sleep(0.1)  # Check for output every 100ms
            except Exception as e:
                print(f"Error in terminal streamer: {e}")
                time.sleep(1)
    
    # Start terminal streaming thread
    terminal_thread = threading.Thread(target=terminal_streamer, daemon=True)
    terminal_thread.start()
    
    return app, socketio