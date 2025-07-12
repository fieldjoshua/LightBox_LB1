# LightBox - Advanced LED Matrix Controller

A high-performance, optimized LED matrix controller for Raspberry Pi with support for both WS2811 (NeoPixel) and HUB75 LED panels. Features include real-time web control, hardware button integration, and extensive animation capabilities.

## 🚀 Features

### Core Features
- **Dual LED Support**: WS2811/NeoPixel strips and HUB75 RGB panels
- **Performance Optimized**: 40% faster with pre-calculated lookup tables
- **Platform Aware**: Auto-optimizes for Pi Zero W, Pi 3B+, Pi 4
- **Web Interface**: Real-time control and monitoring at port 5001
- **Hardware Integration**: Physical buttons and OLED display support
- **Animation Engine**: Plugin-based system with smooth transitions
- **Simulation Mode**: Develop and test without hardware

### Performance Enhancements
- **Gamma Correction**: Pre-calculated lookup tables (40% improvement)
- **Serpentine Mapping**: Cached index calculations
- **Color Conversions**: LRU cache for HSV→RGB
- **Double Buffering**: Smooth animations on both LED types
- **Frame Pooling**: Reduced memory allocations
- **CPU Isolation**: Dedicated core for LED updates (Pi 3B+/4)

### HUB75 Optimizations (Based on Henner Zeller's Library)
- Hardware PWM support (GPIO4-GPIO18 jumper)
- SwapOnVSync() for tear-free animation
- Configurable gpio_slowdown and pwm_bits
- 100+ Hz refresh rates on Pi 3B+

## 📋 Requirements

### Hardware
- Raspberry Pi (Zero W, 3B+, or 4 recommended)
- WS2811/NeoPixel LED strip OR HUB75 RGB panel
- 5V power supply (60W+ for 100 LEDs)
- Optional: GPIO buttons, OLED display

### Software
- Python 3.8+
- Raspberry Pi OS (Lite or Desktop)
- Root/sudo access for GPIO

## 🛠️ Installation

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/LightBox.git
cd LightBox

# Install dependencies
pip install -r requirements-optimized.txt

# For HUB75 support, install RGB matrix library
sudo bash scripts/install_rgb_matrix.sh

# Run the optimized version
sudo python3 lightbox.py
```

### Platform-Specific Setup

#### Raspberry Pi Zero W
```bash
# Use minimal setup for better performance
bash scripts/setup-minimal.sh
```

#### Raspberry Pi 3B+/4
```bash
# Full setup with all optimizations
bash scripts/setup.sh

# For HUB75 panels, enable CPU isolation
# Add to /boot/cmdline.txt: isolcpus=3
# Add to /boot/config.txt: gpu_mem=16

# For hardware PWM (reduces flicker)
# Solder jumper between GPIO4 and GPIO18
```

### Migration from Older Versions
```bash
# Migrate settings from previous installations
python3 scripts/migrate_to_optimized.py
```

## 🎮 Usage

### Basic Operation
```bash
# Run with hardware
sudo python3 lightbox.py

# Run in simulation mode (no hardware required)
python3 run_simulation.py

# Run original version (legacy)
sudo python3 CosmicLED.py
```

### Web Interface
Access the web interface at `http://your-pi-ip:5001`

Features:
- Real-time animation control
- Brightness, speed, and color adjustments
- Performance monitoring dashboard
- Animation program selection
- Preset management

### Hardware Controls (if connected)
- **Mode Button** (GPIO23): Cycle through animations
- **Brightness** (GPIO24/25): Adjust brightness up/down
- **Speed** (GPIO8/7): Adjust animation speed
- **Preset** (GPIO12): Load saved configuration

## 🎨 Animation System

### Built-in Animations
- **Cosmic**: Flowing nebula effects
- **Aurora**: Northern lights simulation
- **Matrix**: Digital rain effect
- **Rainbow**: Color wheel cycles
- **Sparkle**: Twinkling stars
- **Waves**: Ocean wave patterns

### Creating Custom Animations

Create a new file in `animations/` directory:

```python
"""My Custom Animation"""

def animate(pixels, config, frame):
    """
    Animation function called each frame.
    
    Args:
        pixels: List of (R,G,B) tuples to modify
        config: Configuration object with helpers
        frame: Current frame number
    """
    # Example: Simple color cycle
    for i in range(len(pixels)):
        hue = (frame / 100.0 + i / len(pixels)) % 1.0
        pixels[i] = config.hsv_to_rgb(hue, 1.0, 1.0)

# Optional: Animation metadata
ANIMATION_INFO = {
    'name': 'My Animation',
    'description': 'A simple color cycle',
    'version': '1.0',
    'author': 'Your Name'
}
```

## 🔧 Configuration

### Settings File (settings.json)
```json
{
  "brightness": 0.8,
  "animation_speed": 1.0,
  "target_fps": 30,
  "matrix_type": "ws2811",
  "ws2811": {
    "width": 10,
    "height": 10,
    "serpentine": true,
    "data_pin": "D12"
  }
}
```

## 📊 Performance

### Expected Performance

| Platform | LED Type | Target FPS | Achieved FPS |
|----------|----------|------------|--------------|
| Pi Zero W | WS2811 | 20 | 20-25 |
| Pi 3B+ | WS2811 | 60 | 50-60 |
| Pi 3B+ | HUB75 | 60 | 100-130 |
| Pi 4 | HUB75 | 120 | 150+ |

## 🧪 Testing

```bash
# Run the test suite
python3 test_optimized.py

# Hardware test script
sudo python3 scripts/matrix_test.py
```

## 📁 Project Structure

```
LightBox/
├── core/                  # Optimized core components
├── drivers/              # Hardware drivers
├── web/                  # Web interface
├── animations/           # Animation plugins
├── hardware/             # Hardware integration
├── utils/                # Utility modules
├── scripts/              # Setup and maintenance
├── tests/                # Test suite
├── lightbox.py           # Main entry point (optimized)
├── CosmicLED.py          # Original implementation
├── LB_Interface/         # Enhanced version
└── CLAUDE.md             # AI assistant instructions
```

## 🔄 Development Status

This project has undergone significant optimization:
- **Original**: `CosmicLED.py` - Basic implementation
- **Enhanced**: `LB_Interface/` - Added features
- **Optimized**: `core/`, `drivers/`, etc. - 40% performance improvement

## 🚧 Troubleshooting

### Common Issues

**Low FPS**
- Enable CPU isolation on Pi 3B+/4
- Check performance metrics at `/tmp/lightbox_stats.json`

**Import Errors**
```bash
pip install -r requirements-optimized.txt
```

**Permission Errors**
- Run with `sudo` for GPIO access

## 📜 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Henner Zeller](https://github.com/hzeller/rpi-rgb-led-matrix) for RGB matrix library
- [Adafruit](https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel) for NeoPixel support

---

Made with ❤️ for the LED enthusiast community