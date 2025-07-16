from flask import (Blueprint, jsonify, request,
                   render_template, current_app, send_from_directory)
import os
import json
from werkzeug.utils import secure_filename

api_blueprint = Blueprint('api', __name__, template_folder='../web/templates')


def get_led_controller():
    return current_app.led_controller


def allowed_file(filename, file_types=None):
    if file_types is None:
        file_types = {'py'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in file_types


def get_program_parameters(program_path):
    """Extract configurable parameters from a program file"""
    try:
        with open(program_path, 'r') as f:
            content = f.read()

        parameters = {}
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('# PARAM:'):
                param_def = line[8:].strip()
                parts = param_def.split('|')
                if len(parts) >= 4:
                    name, p_type, default, desc = parts[:4]
                    p_min = parts[4] if len(parts) > 4 else None
                    p_max = parts[5] if len(parts) > 5 else None

                    parameters[name] = {
                        'type': p_type,
                        'default': default,
                        'min': p_min,
                        'max': p_max,
                        'description': desc
                    }

        return parameters
    except Exception as e:
        print(f"Error extracting parameters from {program_path}: {e}")
        return {}


@api_blueprint.route('/')
def index():
    return render_template('enhanced.html')


@api_blueprint.route('/api/status')
def get_status():
    led_controller = get_led_controller()
    if led_controller:
        return jsonify({
            'running': led_controller.running,
            'current_program': led_controller.current_program,
            'config': led_controller.config.to_dict(),
            'programs': list(led_controller.programs.keys()),
            'stats': led_controller.stats
        })
    return jsonify({'error': 'LED controller not initialized'}), 503


@api_blueprint.route('/api/config', methods=['POST'])
def update_config():
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503
    try:
        data = request.json
        led_controller.update_config(data)
        led_controller.config.save_settings()
        return jsonify(
            {'success': True, 'config': led_controller.config.to_dict()}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_blueprint.route('/api/program', methods=['POST'])
def switch_program():
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503

    try:
        data = request.json
        program_name = data.get('program')

        if led_controller.switch_program(program_name):
            return jsonify({
                'success': True,
                'current_program': led_controller.current_program
            })
        else:
            return jsonify({'error': 'Invalid program name'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_blueprint.route('/api/upload', methods=['POST'])
def upload_program():
    """Upload new animation program"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        scripts_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(scripts_dir, exist_ok=True)
        filepath = os.path.join(scripts_dir, filename)

        try:
            content = file.read()
            compile(content, filename, 'exec')
            with open(filepath, 'wb') as f:
                f.write(content)
            led_controller = get_led_controller()
            if led_controller:
                led_controller.load_programs()
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'Program uploaded successfully'
            })
        except SyntaxError as e:
            return jsonify({
                'error': f'Invalid Python syntax: {e}'
            }), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({
        'error': 'Invalid file type. Only .py files are allowed'
    }), 400


@api_blueprint.route('/api/program-parameters/<program_name>')
def get_program_params(program_name):
    """Get configurable parameters for a specific program"""
    scripts_dir = current_app.config['UPLOAD_FOLDER']
    program_path = os.path.join(scripts_dir, f"{program_name}.py")

    if os.path.exists(program_path):
        parameters = get_program_parameters(program_path)
    else:
        parameters = {}

    return jsonify({
        'program': program_name,
        'parameters': parameters
    })


@api_blueprint.route('/api/program-parameters/<program_name>', methods=['POST'])
def update_program_parameters(program_name):
    """Update program parameters"""
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503

    try:
        data = request.json
        led_controller.update_program_parameters(program_name, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_blueprint.route('/api/upload-files', methods=['POST'])
def upload_files():
    """Upload multiple files to Pi"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    upload_type = request.form.get('type', 'scripts')
    results = []

    for file in files:
        if file.filename == '':
            continue

        if file and allowed_file(file.filename, {'py', 'txt', 'json', 'md'}):
            filename = secure_filename(file.filename)
            if upload_type == 'presets':
                upload_dir = 'presets'
            elif upload_type == 'config':
                upload_dir = 'config'
            else:
                upload_dir = 'scripts'

            upload_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), upload_dir
            )
            os.makedirs(upload_path, exist_ok=True)
            filepath = os.path.join(upload_path, filename)

            try:
                content = file.read()
                if filename.endswith('.py'):
                    compile(content, filename, 'exec')
                with open(filepath, 'wb') as f:
                    f.write(content)
                results.append({'filename': filename, 'success': True})
            except SyntaxError as e:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'Invalid Python syntax: {e}'
                })
            except Exception as e:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': str(e)
                })
        else:
            results.append({
                'filename': file.filename,
                'success': False,
                'error': 'File type not allowed'
            })

    led_controller = get_led_controller()
    if led_controller and upload_type == 'scripts':
        led_controller.load_programs()

    return jsonify({'results': results})


@api_blueprint.route('/api/files')
def list_files():
    """List files in scripts, presets, and config directories"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    scripts_dir = os.path.join(base_dir, 'scripts')
    presets_dir = os.path.join(base_dir, 'presets')
    config_dir = os.path.join(base_dir, 'config')
    files = {'scripts': [], 'presets': [], 'config': []}
    for folder, key in [(scripts_dir, 'scripts'),
                        (presets_dir, 'presets'),
                        (config_dir, 'config')]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if os.path.isfile(os.path.join(folder, f)):
                    files[key].append(f)
    return jsonify(files)


@api_blueprint.route('/api/files/<path:filepath>', methods=['DELETE'])
def delete_file(filepath):
    """Delete a file from the Pi"""
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        full_path = os.path.join(base_path, filepath)
        allowed_dirs = ['scripts', 'presets', 'config']
        if not any(filepath.startswith(d + '/') for d in allowed_dirs):
            return jsonify({'error': 'Access denied'}), 403
        if os.path.exists(full_path):
            os.remove(full_path)
            if filepath.startswith('scripts/'):
                led_controller = get_led_controller()
                if led_controller:
                    led_controller.load_programs()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/api/files/<path:filepath>')
def download_file(filepath):
    """Download a file from the Pi"""
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        directory = os.path.join(base_path, os.path.dirname(filepath))
        filename = os.path.basename(filepath)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/api/stats')
def get_stats():
    """Get runtime statistics"""
    try:
        if os.path.exists('/tmp/lightbox_stats.json'):
            with open('/tmp/lightbox_stats.json', 'r') as f:
                stats = json.load(f)
            return jsonify(stats)
        return jsonify({'error': 'Stats not available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/api/palettes')
def get_palettes():
    """Get available color palettes"""
    led_controller = get_led_controller()
    if led_controller:
        return jsonify({
            'palettes': list(led_controller.config.PALETTES.keys()),
            'current': led_controller.config.CURRENT_PALETTE
        })
    return jsonify({'error': 'LED controller not initialized'}), 503


@api_blueprint.route('/api/palette', methods=['POST'])
def set_palette():
    """Set active color palette"""
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503

    try:
        data = request.json
        palette_name = data.get('palette')

        if palette_name in led_controller.config.PALETTES:
            led_controller.config.CURRENT_PALETTE = palette_name
            led_controller.config.save_settings()
            return jsonify({'success': True, 'palette': palette_name})
        else:
            return jsonify({'error': 'Invalid palette name'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_blueprint.route('/api/save-preset', methods=['POST'])
def save_preset():
    """Save current settings as a preset"""
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503

    try:
        data = request.json
        preset_name = data.get('name')
        if not preset_name:
            return jsonify({'error': 'Preset name required'}), 400

        led_controller.save_preset(preset_name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api_blueprint.route('/api/load-preset', methods=['POST'])
def load_preset():
    """Load settings from preset"""
    led_controller = get_led_controller()
    if not led_controller:
        return jsonify({'error': 'LED controller not initialized'}), 503

    try:
        data = request.json
        preset_name = data.get('name', 'default')
        preset_file = os.path.join('presets', f"{preset_name}.json")
        if os.path.exists(preset_file):
            with open(preset_file, 'r') as f:
                preset_data = json.load(f)
            led_controller.update_config(preset_data)
            led_controller.config.save_settings()
            return jsonify({'success': True, 'preset': preset_data})
        else:
            return jsonify({'error': 'Preset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/api/presets')
def list_presets():
    """List available presets"""
    try:
        presets_dir = 'presets'
        presets = []
        if os.path.exists(presets_dir):
            for filename in os.listdir(presets_dir):
                if filename.endswith('.json'):
                    presets.append(filename[:-5])
        return jsonify({'presets': presets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 