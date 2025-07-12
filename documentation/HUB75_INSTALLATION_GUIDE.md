# LightBox HUB75 Installation Guide

This guide will walk you through installing and setting up LightBox for use with HUB75 LED matrices on a Raspberry Pi.

## Requirements

- Raspberry Pi (any model, but Pi 3B+ or newer recommended)
- HUB75 LED matrix panel
- Adafruit RGB Matrix Bonnet/HAT or compatible interface
- Power supply appropriate for your LED matrix
- Micro SD card with Raspberry Pi OS installed

## Installation Options

There are two ways to install LightBox:

### Option 1: Automatic Installation (Recommended)

1. SSH into your Raspberry Pi
2. Download the installation script:
   ```bash
   wget https://raw.githubusercontent.com/yourusername/LightBox/main/install_lightbox_hub75.sh
   ```
3. Make the script executable:
   ```bash
   chmod +x install_lightbox_hub75.sh
   ```
4. Run the script as root:
   ```bash
   sudo ./install_lightbox_hub75.sh
   ```

The script will:
- Install all required dependencies
- Set up the RGB Matrix library
- Create the LightBox directory structure
- Install a test animation
- Configure and start the LightBox service

### Option 2: Manual Installation

If you prefer to install manually or the automatic script doesn't work for your setup:

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-dev python3-pillow libatlas-base-dev libopenjp2-7 libtiff5 git build-essential scons libcairo2-dev
   ```

2. Clone the RGB Matrix library:
   ```bash
   git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
   cd rpi-rgb-led-matrix
   make -C examples-api-use
   ```

3. Install the Python binding:
   ```bash
   cd bindings/python
   sudo pip3 install -e .
   ```

4. Download and set up LightBox (replace with your actual download method):
   ```bash
   cd ~
   git clone https://github.com/yourusername/LightBox.git lightbox
   cd lightbox
   ```

5. Install Python requirements:
   ```bash
   pip3 install -r requirements.txt
   ```

6. Run the test animation:
   ```bash
   python3 lightbox.py rainbow_wave
   ```

## Configuration

The main configuration file is located at `/home/pi/lightbox/config.py`. Edit this file to match your LED matrix setup:

```python
# HUB75 Matrix configuration
hub75 = {
    'rows': 64,           # Number of rows (typically 32 or 64)
    'cols': 64,           # Number of columns (typically 32 or 64)
    'chain_length': 1,    # Number of panels daisy-chained together horizontally
    'parallel': 1,        # Number of panels stacked vertically
    'hardware_mapping': 'adafruit-hat',  # Hardware interface type
    'gpio_slowdown': 1,   # GPIO slowdown factor (1 for Pi 3, 2 for Pi 4)
    'brightness': 100     # Brightness level (0-100)
}
```

## Usage

### Running Animations

To run an animation:
```bash
cd /home/pi/lightbox
python3 lightbox.py animation_name
```

To list available animations:
```bash
python3 lightbox.py --list
```

### Service Management

LightBox runs as a systemd service. You can control it with:

```bash
# Check status
sudo systemctl status lightbox

# Start service
sudo systemctl start lightbox

# Stop service
sudo systemctl stop lightbox

# Restart service
sudo systemctl restart lightbox

# Enable at boot
sudo systemctl enable lightbox

# Disable at boot
sudo systemctl disable lightbox
```

## Creating Custom Animations

To create a custom animation, add a Python file to the `/home/pi/lightbox/scripts/` directory. The file should contain an `animate` function with the following signature:

```python
def animate(pixels, config, frame):
    """
    Your animation code here
    
    Args:
        pixels: List of (r,g,b) tuples to modify
        config: Configuration object with matrix dimensions
        frame: Current frame number
    """
    # Animation code
```

See the included `rainbow_wave.py` animation for an example.

## Troubleshooting

### Common Issues

#### Matrix Not Displaying

1. Check power connections - ensure your matrix has adequate power
2. Verify GPIO connections between the Pi and matrix
3. Check your config.py settings match your actual hardware
4. Try different `hardware_mapping` values in config.py

#### Installation Errors

1. **libtiff5 package not found**: The installation script now automatically detects and uses the appropriate libtiff package available on your system. If you're installing manually, try using `libtiff` instead of `libtiff5`, or find the available package with `apt-cache search libtiff`.

2. **pip installation errors**: If you encounter "externally-managed-environment" errors with pip:
   - For newer pip versions (23.0+), the script uses the `--break-system-packages` flag
   - For older pip versions, this flag is omitted
   - If installing manually, try using a virtual environment:
     ```bash
     python3 -m venv lightbox_env
     source lightbox_env/bin/activate
     pip install -r requirements.txt
     ```

3. **RGB Matrix library installation fails**: Make sure you have the required build tools:
   ```bash
   sudo apt-get install -y build-essential scons libcairo2-dev
   ```

#### Poor Performance

1. Adjust the `gpio_slowdown` value in config.py:
   - For Pi 4: use 2
   - For Pi 3: use 1
   - For Pi 2 or earlier: use 0 or 1

2. Reduce the complexity of your animations or lower the FPS setting

#### Flickering Display

1. Check power supply - inadequate power causes flickering
2. Try different `hardware_mapping` settings
3. Adjust `gpio_slowdown` value

### Getting Help

If you encounter issues not covered here, please:
1. Check the project's GitHub issues
2. Join our community forum at [forum URL]
3. Submit a detailed bug report including:
   - Your Raspberry Pi model
   - LED matrix type and size
   - Error messages
   - Steps to reproduce the issue

## Advanced Configuration

For advanced configuration options and performance tuning, see the [HUB75 Performance Guide](HUB75_PERFORMANCE_GUIDE.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

If the animation seems off, there could be a few issues to check:

1. **Color or brightness issues**:
   - Try adjusting the brightness in config.py:
     ```python
     hub75 = {
         # other settings...
         'brightness': 70,  # Try a lower value like 70 instead of 100
     }
     ```

2. **Flickering or unstable display**:
   - Try increasing the GPIO slowdown:
     ```python
     hub75 = {
         # other settings...
         'gpio_slowdown': 2,  # Try 2 or 3 instead of 1
     }
     ```

3. **Panel orientation issues**:
   - If the display appears rotated or flipped, we can add options to fix it:
     ```python
     # In simple_lightbox.py, add these options before creating the matrix:
     options.led_rgb_sequence = "RGB"  # Try "BGR" if colors seem wrong
     options.disable_hardware_pulsing = True  # Can help with flickering
     ```

4. **Panel type mismatch**:
   - If you're using a different panel type, try other hardware mappings:
     ```python
     hub75 = {
         # other settings...
         'hardware_mapping': 'regular',  # Try 'regular' instead of 'adafruit-hat'
     }
     ```

Let's modify the simple_lightbox.py script to add some adjustment options:

```bash
cd ~/lightbox
cat > simple_lightbox.py << 'EOL'
#!/usr/bin/env python3
"""
Simple LightBox - LED Matrix Controller with adjustments
"""

import time
import sys
import colorsys
import argparse
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import config

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simple LightBox Controller")
    parser.add_argument("--brightness", type=int, help="Brightness (1-100)")
    parser.add_argument("--slowdown", type=int, help="GPIO Slowdown (0-4)")
    parser.add_argument("--rgb", choices=["RGB", "RBG", "GRB", "GBR", "BRG", "BGR"], help="RGB sequence")
    parser.add_argument("--no-hardware-pulse", action="store_true", help="Disable hardware pulsing")
    args = parser.parse_args()
    
    # Set up the matrix
    options = RGBMatrixOptions()
    options.rows = config.hub75['rows']
    options.cols = config.hub75['cols']
    options.chain_length = config.hub75['chain_length']
    options.parallel = config.hub75['parallel']
    options.hardware_mapping = config.hub75['hardware_mapping']
    
    # Apply command line overrides
    options.gpio_slowdown = args.slowdown if args.slowdown is not None else config.hub75['gpio_slowdown']
    options.brightness = args.brightness if args.brightness is not None else config.hub75['brightness']
    
    if args.rgb:
        options.led_rgb_sequence = args.rgb
    
    if args.no_hardware_pulse:
        options.disable_hardware_pulsing = True
    
    print(f"Using settings: brightness={options.brightness}, slowdown={options.gpio_slowdown}")
    if hasattr(options, 'led_rgb_sequence'):
        print(f"RGB sequence: {options.led_rgb_sequence}")
    if hasattr(options, 'disable_hardware_pulsing'):
        print(f"Hardware pulsing disabled: {options.disable_hardware_pulsing}")
    
    # Create the matrix
    try:
        matrix = RGBMatrix(options=options)
        print(f"Matrix initialized: {config.matrix_width}x{config.matrix_height}")
    except Exception as e:
        print(f"Error initializing matrix: {e}")
        sys.exit(1)
    
    # Create pixel buffer
    width = config.matrix_width
    height = config.matrix_height
    pixels = [(0, 0, 0)] * (width * height)
    
    # Animation loop
    try:
        frame = 0
        while True:
            start_time = time.time()
            
            # Generate rainbow wave
            for y in range(height):
                for x in range(width):
                    # Calculate hue based on position and time
                    hue = (x + y) / (width + height) + frame * 0.005
                    hue = hue % 1.0
                    
                    # Convert HSV to RGB
                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                    
                    # Scale to 0-255 range
                    r = int(r * 255)
                    g = int(g * 255)
                    b = int(b * 255)
                    
                    # Set pixel color
                    pixel_index = y * width + x
                    pixels[pixel_index] = (r, g, b)
            
            # Update matrix
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    r, g, b = pixels[idx]
                    matrix.SetPixel(x, y, r, g, b)
            
            # Calculate timing
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0/30 - elapsed)
            
            # Sleep to maintain frame rate
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Update frame counter
            frame += 1
            
            # Print FPS every 100 frames
            if frame % 100 == 0:
                actual_fps = 1.0 / (elapsed + sleep_time)
                print(f"Frame: {frame}, FPS: {actual_fps:.1f}")
    
    except KeyboardInterrupt:
        print("Animation stopped by user")
    except Exception as e:
        print(f"Error in animation loop: {e}")
    finally:
        matrix.Clear()
        print("Animation stopped")

if __name__ == "__main__":
    main()
EOL

chmod +x simple_lightbox.py
```

Now you can try different settings to fix the display:

1. Try increasing the GPIO slowdown:
   ```bash
   sudo python3 simple_lightbox.py --slowdown 2
   ```

2. Try different RGB sequences if colors look wrong:
   ```bash
   sudo python3 simple_lightbox.py --rgb BGR
   ```

3. Try disabling hardware pulsing:
   ```bash
   sudo python3 simple_lightbox.py --no-hardware-pulse
   ```

4. Try a lower brightness:
   ```bash
   sudo python3 simple_lightbox.py --brightness 70
   ```

Once you find settings that work well, update your config.py file with those values, and then update the systemd service to use those parameters. 

Let's use the existing web GUI from the project. Based on the search results, the best option appears to be:
`/LB_Interface/LightBox/webgui/app_hub75_fixed.py` which has HUB75 support.

Let's set up the existing web GUI for your installation:

1. First, let's create the necessary directory structure:

```bash
cd ~/lightbox
mkdir -p webgui/templates webgui/static
```

2. Let's copy the app_hub75_fixed.py file:

```bash
cd ~/lightbox
cat > webgui/app.py << 'EOL'
#!/usr/bin/env python3
"""
LightBox Web Interface - HUB75 Fixed Version
"""

import os
import sys
import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import threading
import importlib

def create_app(conductor=None, config=None):
    app = Flask(__name__)
    
    # Store conductor and config
    app.conductor = conductor
    app.config_module = config
    
    # Track active animations
    app.active_animation = None
    app.animation_running = False
    app.animation_thread = None
    
    @app.route('/')
    def index():
        """Render the main interface"""
        return render_template('index.html')
    
    @app.route('/static/<path:path>')
    def send_static(path):
        """Serve static files"""
        return send_from_directory('static', path)
    
    @app.route('/api/animations')
    def get_animations():
        """Get list of available animations"""
        animations = []
        scripts_dir = Path("scripts")
        
        if scripts_dir.exists():
            for script_path in scripts_dir.glob("*.py"):
                name = script_path.stem
                # Try to get animation parameters
                try:
                    spec = importlib.util.spec_from_file_location(name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    params = getattr(module, 'PARAMS', {})
                    if not params:
                        params = {
                            "name": name,
                            "description": "Animation script",
                            "speed_min": 0.1,
                            "speed_max": 5.0,
                            "speed_default": 1.0
                        }
                    
                    animations.append({
                        "id": name,
                        "name": params.get("name", name),
                        "description": params.get("description", ""),
                        "speed_min": params.get("speed_min", 0.1),
                        "speed_max": params.get("speed_max", 5.0),
                        "speed_default": params.get("speed_default", 1.0)
                    })
                except Exception as e:
                    print(f"Error loading animation {name}: {e}")
                    animations.append({
                        "id": name,
                        "name": name,
                        "description": f"Error loading: {str(e)}",
                        "speed_min": 0.1,
                        "speed_max": 5.0,
                        "speed_default": 1.0
                    })
        
        return jsonify(animations)
    
    @app.route('/api/config')
    def get_config():
        """Get current configuration"""
        if app.config_module:
            config_data = {
                "matrix": {
                    "width": app.config_module.matrix_width,
                    "height": app.config_module.matrix_height,
                },
                "hub75": {
                    "rows": app.config_module.hub75['rows'],
                    "cols": app.config_module.hub75['cols'],
                    "chain_length": app.config_module.hub75['chain_length'],
                    "parallel": app.config_module.hub75['parallel'],
                    "hardware_mapping": app.config_module.hub75['hardware_mapping'],
                    "gpio_slowdown": app.config_module.hub75['gpio_slowdown'],
                    "brightness": app.config_module.hub75['brightness']
                },
                "fps": app.config_module.fps,
                "speed": app.config_module.speed
            }
            return jsonify(config_data)
        return jsonify({"error": "Configuration not available"})
    
    @app.route('/api/start', methods=['POST'])
    def start_animation():
        """Start an animation"""
        data = request.json
        animation_name = data.get('animation')
        
        if not animation_name:
            return jsonify({"error": "No animation specified"})
        
        # If we have a conductor, use it
        if app.conductor:
            success = app.conductor.start(animation_name)
            return jsonify({"success": success, "animation": animation_name})
        
        # Otherwise, start our own animation thread
        try:
            # Stop any running animation
            if app.animation_thread and app.animation_thread.is_alive():
                app.animation_running = False
                app.animation_thread.join(timeout=1.0)
            
            # Load the animation module
            animation_path = Path(f"scripts/{animation_name}.py")
            if not animation_path.exists():
                return jsonify({"error": f"Animation not found: {animation_name}"})
            
            spec = importlib.util.spec_from_file_location(animation_name, animation_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'animate'):
                return jsonify({"error": f"Animation {animation_name} does not have an animate function"})
            
            app.active_animation = module
            app.animation_running = True
            
            # Start animation thread
            app.animation_thread = threading.Thread(target=run_animation_thread)
            app.animation_thread.daemon = True
            app.animation_thread.start()
            
            return jsonify({"success": True, "animation": animation_name})
        except Exception as e:
            return jsonify({"error": str(e)})
    
    @app.route('/api/stop', methods=['POST'])
    def stop_animation():
        """Stop the current animation"""
        if app.conductor:
            app.conductor.stop()
            return jsonify({"success": True})
        
        app.animation_running = False
        if app.animation_thread and app.animation_thread.is_alive():
            app.animation_thread.join(timeout=1.0)
        
        return jsonify({"success": True})
    
    @app.route('/api/brightness', methods=['POST'])
    def set_brightness():
        """Set matrix brightness"""
        data = request.json
        brightness = data.get('brightness')
        
        if brightness is None:
            return jsonify({"error": "No brightness specified"})
        
        try:
            brightness = int(brightness)
            if brightness < 0 or brightness > 100:
                return jsonify({"error": "Brightness must be between 0 and 100"})
            
            if app.config_module:
                app.config_module.hub75['brightness'] = brightness
                
                # If we have a conductor, update its matrix driver
                if app.conductor and app.conductor.matrix_driver and app.conductor.matrix_driver.driver:
                    if hasattr(app.conductor.matrix_driver.driver.matrix, 'SetBrightness'):
                        app.conductor.matrix_driver.driver.matrix.SetBrightness(brightness)
            
            return jsonify({"success": True, "brightness": brightness})
        except Exception as e:
            return jsonify({"error": str(e)})
    
    @app.route('/api/speed', methods=['POST'])
    def set_speed():
        """Set animation speed"""
        data = request.json
        speed = data.get('speed')
        
        if speed is None:
            return jsonify({"error": "No speed specified"})
        
        try:
            speed = float(speed)
            if app.config_module:
                app.config_module.speed = speed
            
            return jsonify({"success": True, "speed": speed})
        except Exception as e:
            return jsonify({"error": str(e)})
    
    def run_animation_thread():
        """Run animation in a separate thread"""
        if not app.active_animation or not app.config_module:
            return
        
        # Create pixel buffer
        width = app.config_module.matrix_width
        height = app.config_module.matrix_height
        pixels = [(0, 0, 0)] * (width * height)
        
        # Import matrix driver
        try:
            from drivers.matrix_driver import MatrixDriver
            matrix_driver = MatrixDriver(app.config_module)
        except Exception as e:
            print(f"Error initializing matrix driver: {e}")
            return
        
        # Animation loop
        frame = 0
        frame_interval = 1.0 / app.config_module.fps
        
        while app.animation_running:
            start_time = time.time()
            
            # Update animation
            app.active_animation.animate(pixels, app.config_module, frame)
            
            # Update matrix
            matrix_driver.update(pixels)
            
            # Calculate timing
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            
            # Sleep to maintain frame rate
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Update frame counter
            frame += 1
        
        # Clean up
        matrix_driver.clear()
    
    return app

if __name__ == '__main__':
    # If run directly, create a standalone app
    import config
    app = create_app(None, config)
    app.run(host='0.0.0.0', port=5000, debug=True)
EOL
```

3. Now, let's create the HTML template:

```bash
cd ~/lightbox
cat > webgui/templates/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LightBox HUB75 Controller</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #121212;
            color: #eee;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #222;
            padding: 15px;
            text-align: center;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        h1 {
            margin: 0;
            color: #0f0;
        }
        .card {
            background-color: #1e1e1e;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .card h2 {
            margin-top: 0;
            color: #0f0;
        }
        select, button, input {
            