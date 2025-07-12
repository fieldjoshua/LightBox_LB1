# LightBox - Advanced LED Matrix Controller

A high-performance, optimized LED matrix controller for Raspberry Pi with support for both WS2811 (NeoPixel) and HUB75 LED panels. Features include real-time web control, hardware button integration, and extensive animation capabilities.

## Features

- 🎨 **Multiple Animation Programs**: Built-in animations plus support for custom scripts
- 🌐 **Web Control Panel**: Full-featured web interface for remote control
- 🎮 **Hardware Integration**: Support for physical buttons and OLED display
- 💾 **Preset System**: Save and load your favorite configurations
- 📊 **Live Statistics**: Real-time FPS, uptime, and performance monitoring
- 🎯 **Color Palettes**: Multiple pre-defined palettes with smooth interpolation
- 📤 **Program Upload**: Upload custom animations through the web interface

## Hardware Requirements

- Raspberry Pi (3B+, 4, or Zero 2 W recommended)
- WS2811/WS2812B LED strip (configured for 10x10 matrix, 100 LEDs)
- 5V power supply (minimum 6A for 100 LEDs at full brightness)
- Level shifter (3.3V to 5V) for reliable data signal
- Optional: GPIO buttons for physical control
- Optional: SSD1306 OLED display for status

### LED Matrix Wiring (Serpentine/Zigzag)

The system is configured for serpentine (back-and-forth) wiring:
```
Row 0: → 0  1  2  3  4  5  6  7  8  9
Row 1: ← 19 18 17 16 15 14 13 12 11 10
Row 2: → 20 21 22 23 24 25 26 27 28 29
Row 3: ← 39 38 37 36 35 34 33 32 31 30
...and so on
```

To change to progressive wiring (all rows left-to-right), edit `config.py`:
```python
SERPENTINE = False  # Set to False for progressive wiring
```

## Installation

1. **Clone or copy this repository to your Raspberry Pi**

2. **Run the setup script:**
   ```bash
   cd LightBox
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Connect your LED strip:**
   - Data wire to GPIO12 (Pin 32)
   - Ground to GND
   - 5V to external power supply (NOT the Pi's 5V pin!)
   - Connect power supply ground to Pi ground

## Usage

### Starting LightBox

```bash
sudo ./venv/bin/python3 CosmicLED.py
```

**Note**: `sudo` is required for GPIO access.

### Web Interface

Once running, access the control panel at:
```
http://[your-pi-ip]:5000
```

Features available:
- Switch between animation programs
- Adjust brightness, speed, scale, intensity, and gamma
- Select color palettes
- Save/load presets
- Upload custom animations
- Monitor live statistics

### Auto-Start on Boot

To run LightBox automatically on startup:

```bash
sudo cp lightbox.service /etc/systemd/system/
sudo systemctl enable lightbox
sudo systemctl start lightbox
```

## Creating Custom Animations

Create Python files in the `scripts/` directory with an `animate` function:

```python
def animate(pixels, config, frame):
    """Your animation logic here
    
    Args:
        pixels: NeoPixel object to control LEDs
        config: Configuration object with settings
        frame: Current frame number
    """
    # Example using x,y coordinates with serpentine mapping
    for y in range(config.MATRIX_HEIGHT):
        for x in range(config.MATRIX_WIDTH):
            # Get LED index for serpentine wiring
            i = config.xy_to_index(x, y)
            if i is None:
                continue
            
            # Your color logic here
            pixels[i] = (red, green, blue)
    
    # Or work with raw indices
    for i in range(config.LED_COUNT):
        # Get x,y coordinates from index
        x, y = config.index_to_xy(i)
        # Set pixel colors
        pixels[i] = (red, green, blue)
```

### Available Config Properties

- `config.LED_COUNT`: Number of LEDs (100)
- `config.BRIGHTNESS`: Global brightness (0.0-1.0)
- `config.SPEED`: Animation speed multiplier
- `config.SCALE`: Size/zoom factor
- `config.INTENSITY`: Color intensity
- `config.GAMMA`: Gamma correction value
- `config.interpolate_palette(position)`: Get interpolated color from current palette

## GPIO Button Configuration

If using physical buttons, connect to these GPIO pins:

- **Mode** (GPIO23): Switch animation program
- **Brightness Up** (GPIO24): Increase brightness
- **Brightness Down** (GPIO25): Decrease brightness
- **Speed Up** (GPIO8): Increase animation speed
- **Speed Down** (GPIO7): Decrease animation speed
- **Preset** (GPIO12): Cycle through saved presets

## OLED Display

If using an SSD1306 OLED display:
- Connect via I2C (SDA to GPIO2, SCL to GPIO3)
- Display shows current mode, FPS, brightness, speed, palette, and uptime

## Configuration Files

- `config.py`: Main configuration and color palettes
- `settings.json`: Saved user settings
- `presets/*.json`: Saved preset configurations

## Troubleshooting

### No LEDs lighting up
- Check power connections and ensure ground is shared
- Verify GPIO18 connection
- Try reducing brightness in settings

### Flickering or glitches
- Use a level shifter for reliable 5V data signal
- Ensure adequate power supply
- Check for loose connections

### Web interface not accessible
- Check firewall settings
- Ensure port 5000 is not blocked
- Verify Pi's IP address

### Permission denied errors
- Make sure to run with `sudo`
- Check file permissions

## Performance Tips

- Keep LED count reasonable for smooth animations
- Use appropriate power supply (60mA per LED at full white)
- Consider active cooling for Pi during extended use
- Adjust FPS target in code if needed

## Safety Notes

⚠️ **Important Safety Information**:
- Never power LEDs through the Pi's 5V pin
- Always use an appropriate fuse
- Ensure proper ventilation
- Be cautious of current draw at full brightness

## License

This project is provided as-is for personal and educational use.

## Support

For issues or questions, please check the documentation or create an issue in the project repository.