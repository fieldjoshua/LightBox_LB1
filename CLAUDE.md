# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LightBox is a HUB75 LED Matrix Controller system for Raspberry Pi with real-time web GUI control. The project has recently undergone major performance optimizations (v2.5.0) achieving 8-9x performance improvements.

## Architecture

### Core Components
- **Entry Point**: `lightbox.py` → calls `core.conductor.main()`
- **Main Controller**: `core/conductor.py` - Animation orchestrator
- **Hardware Interface**: `drivers/hub75_driver.py` - HUB75 matrix driver using rpi-rgb-led-matrix
- **Web Interface**: `web/app_simple.py` - Flask server for real-time control
- **Animation Engine**: `core/optimized_animation_loop.py` - Performance-optimized rendering

### Key Directories
- `/core/` - Core engine (conductor, config, performance monitoring)
- `/drivers/` - Hardware drivers (hub75, ws2811, mock)
- `/hardware/` - Physical hardware management (buttons, OLED)
- `/web/` - Web GUI (Flask app, templates, static assets)
- `/scripts/` - Animation scripts (plasma, fire, waves, etc.)
- `/config/` - Configuration files (settings.json)

## Development Commands

### Local Development (Mock Mode)
```bash
# Setup development environment
./setup_venv_dev.sh
source venv/bin/activate

# Run in mock mode (no hardware required)
python lightbox.py

# Run tests
python test_system.py
python test_lightbox_system.py
```

### Raspberry Pi Deployment
```bash
# Initial setup on Pi
./setup_venv_pi.sh
sudo bash install_rgb_matrix.sh

# Deploy to Pi
./deploy_to_pi.sh
# Alternative: ./deploy_via_tailscale.sh or ./deploy_via_usb.sh

# Run on Pi
sudo python3 lightbox.py
```

### Code Quality
```bash
# Lint with ruff (configured in pyproject.toml)
ruff check .
ruff format .
```

## Configuration

Main configuration in `/config/settings.json`:
- `platform`: "hub75" or "ws2811"
- `hub75`: Matrix settings (rows, cols, gpio_slowdown, pwm_bits)
- `performance`: FPS targets, buffer pools, CPU isolation
- `web`: Server host/port settings

## Hardware Requirements

- Raspberry Pi 3B+ or 4
- Adafruit RGB Matrix HAT/Bonnet
- HUB75 LED panel (64x64 recommended)
- 5V power supply for LED panel
- Optional: Hardware PWM (solder GPIO4-GPIO18 jumper)

## Performance Considerations

- The system uses hardware PWM when available
- Double buffering prevents tearing
- Frame pooling reduces memory allocation
- CPU isolation (`isolcpus=3`) improves timing
- Target 30 FPS for smooth animation

## Testing

No formal test framework is configured. Test files are standalone Python scripts:
- `test_system.py` - System integration tests
- `test_lightbox_system.py` - LightBox-specific tests
- Run with mock driver for development testing

## Current State

- Branch: `cleanup/archive-legacy` (archiving old implementations)
- Recent focus: Performance optimization and code cleanup
- Version 2.5.0 deployed with major performance improvements

## CRITICAL HUB75 Performance Optimizations

These optimizations MUST be applied in all builds for maximum performance:

### Hardware Modifications
1. **Quality Mode PWM**: Solder GPIO4-GPIO18 jumper on Adafruit HAT for hardware PWM
   - Enables `adafruit-hat-pwm` mapping (vs standard `adafruit-hat`)
   - Eliminates flicker and timing glitches
   - Disables Pi audio output (add `dtparam=audio=off` to `/boot/config.txt`)

### Software Configuration
1. **GPIO Timing**: `--led-slowdown-gpio=1` for Pi 3B+ (use 3-4 for Pi 4)
2. **PWM Settings**: 
   - Start with `--led-pwm-bits=11` for full color depth
   - Reduce to 7-9 bits if refresh rate too low
   - Enable `--led-pwm-dither-bits=1` to simulate extra color depth
3. **Real-time Priority**: Always run with `sudo` for hardware access
4. **Show Refresh Rate**: Use `--led-show-refresh` during testing
5. **Brightness**: Set `--led-brightness=50-80` for indoor use (saves power/heat)

### System-Level Optimizations
1. **CPU Isolation**: Add `isolcpus=3` to `/boot/cmdline.txt` to dedicate core 3
2. **Performance Governor**: Lock CPU frequency for consistent timing
3. **Disable Audio**: Set `dtparam=audio=off` in `/boot/config.txt`
4. **Minimal OS**: Use Raspberry Pi OS Lite (no desktop) for best performance

### Power Requirements
- **5V Supply**: Minimum 4A for single panel, 10A for multiple
- **Separate Power**: Power Pi and LED panels from separate supplies
- **Terminal Block**: Use HAT's screw terminals for secure connections
- **Panel Power**: For chains >2 panels, feed power to each panel directly

### Expected Performance
With these optimizations on Pi 3B+:
- 64x64 panel: 200-400Hz refresh at 7-9 bit color
- Full 11-bit color: 100-200Hz refresh
- Multiple panels: Use parallel chains if possible (requires special hardware)