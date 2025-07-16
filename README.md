# LightBox Organized - HUB75 LED Matrix Controller

A unified, organized system for controlling HUB75 LED matrices on Raspberry Pi with real-time web GUI control.

## Overview

This system integrates all the building blocks from the original LightBox project into a clean, organized structure that implements the recommendations from the enhancement structure document. It provides:

- **Hardware-accelerated HUB75 driver** with Henner Zeller optimizations
- **Real-time web GUI** for remote control and monitoring
- **Animation engine** with performance optimizations
- **Hardware management** (buttons, OLED display)
- **Comprehensive configuration** system

## Directory Structure

```
LightBox_Organized/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── install_rgb_matrix.sh  # HUB75 library installer
├── lightbox.service       # Systemd service file
├── config/
│   └── settings.json      # Main configuration
├── core/                  # Core animation engine
│   ├── conductor.py       # Animation controller
│   ├── config.py         # Configuration manager
│   ├── performance.py    # Performance monitoring
│   └── matrix_controller.py
├── drivers/              # Hardware drivers
│   ├── hub75_driver.py   # HUB75 optimized driver
│   ├── matrix_driver.py  # Base matrix driver
│   └── ws2811_driver.py  # WS2811 driver
├── hardware/             # Hardware management
│   ├── hardware_manager.py
│   ├── buttons.py        # Button input handling
│   └── oled.py          # OLED display
├── web/                  # Web GUI
│   ├── app.py           # Flask application
│   ├── static/          # CSS/JS assets
│   └── templates/       # HTML templates
├── utils/               # Utility functions
│   ├── color_utils.py   # Color manipulation
│   └── frame_utils.py   # Frame processing
├── scripts/             # Animation scripts
│   ├── parametric_waves.py
│   ├── shimmer.py
│   └── symmetry.py
├── animations/          # Additional animations
├── fonts/              # Font files
├── images/             # Image assets
├── tests/              # Test suite
└── documentation/       # Documentation
```

## Features

### Hardware Support
- **HUB75 RGB Matrix** (64x64, 32x32, etc.)
- **Adafruit RGB Matrix HAT/Bonnet**
- **Raspberry Pi 3B+/4** optimized
- **Hardware PWM** detection and configuration
- **CPU isolation** for dedicated matrix updates

### Web GUI
- **Real-time control** via web browser
- **Animation switching** and parameter adjustment
- **File upload** for custom animations
- **Performance monitoring** and statistics
- **Preset management** and saving

### Animation Engine
- **Double buffering** for tear-free animation
- **Performance optimization** with frame pooling
- **Multiple animation types** (waves, particles, text)
- **Color palette** system with interpolation
- **Gamma correction** and color management

### Configuration
- **JSON-based** configuration system
- **Runtime parameter** adjustment
- **Hardware detection** and auto-configuration
- **Preset saving/loading**

## Installation

### 1. Prerequisites
- Raspberry Pi 3B+ or 4
- Adafruit RGB Matrix HAT/Bonnet
- HUB75 LED panel (64x64 recommended)
- 5V power supply for LED panel

### 2. Install HUB75 Library
```bash
# Run the installer script
sudo bash install_rgb_matrix.sh
```

### 3. Install Python Dependencies

#### For Raspberry Pi
```bash
# Use the provided setup script
./setup_venv_pi.sh

# Activate the virtual environment
source venv/bin/activate
```

#### For Development Environment (non-Raspberry Pi)
```bash
# Use the development setup script
./setup_venv_dev.sh

# Activate the virtual environment
source venv/bin/activate
```

### 4. Configure Hardware
- Connect HUB75 panel to Adafruit HAT
- Power the panel with 5V supply
- For best performance, solder GPIO4-GPIO18 jumper (hardware PWM)

### 5. Start LightBox
```bash
# Run directly
sudo python3 main.py

# Or install as service
sudo cp lightbox.service /etc/systemd/system/
sudo systemctl enable lightbox
sudo systemctl start lightbox
```

## Configuration

Edit `config/settings.json` to customize:

### HUB75 Settings
```json
"hub75": {
  "rows": 64,
  "cols": 64,
  "gpio_slowdown": 4,
  "pwm_bits": 11,
  "hardware_mapping": "adafruit-hat"
}
```

### Performance Settings
```json
"performance": {
  "target_fps": 30,
  "buffer_pool_size": 3,
  "cpu_isolation": true
}
```

### Web Settings
```json
"web": {
  "host": "0.0.0.0",
  "port": 5000,
  "debug": false
}
```

## Usage

### Web Interface
1. Start LightBox: `sudo python3 main.py`
2. Open browser: `http://raspberry-pi-ip:5000`
3. Use web interface to:
   - Switch animations
   - Adjust parameters
   - Upload custom scripts
   - Monitor performance

### Hardware Controls
- **Buttons**: Physical button control (if configured)
- **OLED**: Status display (if connected)
- **Emergency Stop**: Hardware emergency stop

### Animation Scripts
Create custom animations in `scripts/` directory:

```python
def animate(pixels, config, frame):
    """Custom animation function"""
    width = config.get('matrix_width', 64)
    height = config.get('matrix_height', 64)
    
    for y in range(height):
        for x in range(width):
            idx = config.xy_to_index(x, y)
            # Your animation logic here
            pixels[idx] = (r, g, b)
```

## Performance Optimization

### Hardware Optimizations
1. **Hardware PWM**: Solder GPIO4-GPIO18 jumper
2. **CPU Isolation**: Add `isolcpus=3` to `/boot/cmdline.txt`
3. **Audio Disable**: Add `dtparam=audio=off` to `/boot/config.txt`

### Software Optimizations
1. **Double Buffering**: Always use `SwapOnVSync()`
2. **Frame Pooling**: Reuse frame buffers
3. **Lookup Tables**: Pre-compute expensive calculations
4. **Efficient Loops**: Use optimized iteration patterns

## Troubleshooting

### Common Issues
1. **Flickering**: Enable hardware PWM or adjust `gpio_slowdown`
2. **Low Performance**: Enable CPU isolation and optimize animations
3. **Web Interface Not Loading**: Check firewall and port settings
4. **GPIO Errors**: Run with `sudo` for hardware access

### Debug Mode
```bash
# Enable debug logging
sudo python3 main.py --debug

# Check logs
tail -f lightbox.log
```

## Development

### Adding New Animations
1. Create script in `scripts/` directory
2. Implement `animate(pixels, config, frame)` function
3. Use `config.get()` for parameters
4. Use `config.xy_to_index()` for coordinate mapping

### Extending Hardware Support
1. Add driver in `drivers/` directory
2. Inherit from `MatrixDriver` base class
3. Implement required methods
4. Update configuration system

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Henner Zeller** for the rpi-rgb-led-matrix library
- **Adafruit** for the RGB Matrix HAT/Bonnet
- **Raspberry Pi Foundation** for the hardware platform 