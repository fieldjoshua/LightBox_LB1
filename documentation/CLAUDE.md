# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Guidelines

- Do not mislead me with explanations that are false. Tell me what you are actually doing.

## AICheck Integration

Claude should follow the rules specified in `.aicheck/RULES.md` and use AICheck commands:

- `./aicheck action new ActionName` - Create a new action 
- `./aicheck action set ActionName` - Set the current active action
- `./aicheck action complete [ActionName]` - Complete an action with dependency verification
- `./aicheck exec` - Toggle exec mode for system maintenance
- `./aicheck status` - Show the current action status
- `./aicheck dependency add NAME VERSION JUSTIFICATION [ACTION]` - Add external dependency
- `./aicheck dependency internal DEP_ACTION ACTION TYPE [DESCRIPTION]` - Add internal dependency
- `./aicheck todo` - Manage todo lists (your claude to do)

## Development Commands

### Running the System

**Primary Entry Points (Optimized Implementation):**
- **Main application**: `sudo python3 lightbox.py` (requires root for GPIO)
- **Simulation mode**: `python3 run_simulation.py` (no hardware required)
- **Legacy version**: `sudo python3 CosmicLED.py` (original WS2811-only implementation)

**Testing:**
- **Primary test suite**: `python3 test_optimized.py` (comprehensive tests, currently 6/7 passing)
- **Platform detection**: `python3 debug_platform.py`
- **Single test**: `pytest tests/test_hub75_driver.py -v`
- **Performance benchmarks**: `pytest tests/benchmarks/performance_benchmarks.py -v`

### Setup and Installation

**Setup Scripts:**
- **Full setup (Pi 3B+/4)**: `chmod +x setup.sh && ./setup.sh`
- **Minimal setup (Pi Zero W)**: `bash scripts/setup-minimal.sh`
- **HUB75 matrix support**: `sudo bash scripts/install_rgb_matrix.sh`

**Dependencies:**
- **Core**: `pip install -r requirements-optimized.txt`
- **Legacy**: `pip install -r requirements.txt`
- **Minimal**: `pip install adafruit-blinka adafruit-circuitpython-neopixel RPi.GPIO flask`

### Service Management

- **Install systemd service**: `sudo cp lightbox.service /etc/systemd/system/ && sudo systemctl enable lightbox`
- **Start/stop service**: `sudo systemctl {start|stop|restart} lightbox`
- **View logs**: `sudo journalctl -u lightbox -f`
- **Check status**: `sudo systemctl status lightbox`

## Architecture Overview

### Current State: Optimized Multi-Platform Implementation

The project has undergone significant optimization with a **unified codebase** supporting multiple hardware platforms:

**Core Architecture:**
- `lightbox.py` - **Primary entry point** (optimized unified interface)
- `core/conductor.py` - **Main controller** with performance optimizations
- `core/config.py` - **Configuration management** with caching and platform detection
- `core/performance.py` - **Performance monitoring** and metrics collection

**Hardware Abstraction:**
- `drivers/matrix_driver.py` - **Base driver interface**
- `drivers/ws2811_driver.py` - **NeoPixel/WS2811 implementation**
- `drivers/hub75_driver.py` - **HUB75 RGB panel implementation**

**Platform Support:**
- **Pi Zero W**: String lights, 20-25 FPS target, minimal dependencies
- **Pi 3B+/4**: LED matrices, 60 FPS (WS2811) or 130+ Hz (HUB75), full optimizations
- **macOS/Linux**: Simulation mode for development and testing

### Performance Optimizations (Completed)

**Key Improvements:**
- **40% performance boost** via gamma correction lookup tables
- **Serpentine coordinate caching** for efficient matrix mapping
- **HSV to RGB conversion caching** with LRU cache
- **Platform-specific optimizations** based on detected hardware
- **Double buffering** for smooth animations (HUB75)
- **CPU isolation** support for Pi 3B+/4 (`isolcpus=3`)

### Animation System

**Extensive Animation Library:**
- **825 total animations** across multiple optimization levels
- **450 "perfect_75" series** - highly optimized variants
- **Standard API**: `def animate(pixels, config, frame):`
- **Hot-swappable**: Dynamic loading without restart

**Animation Development:**
```python
def animate(pixels, config, frame):
    # Access matrix coordinates: config.xy_to_index(x, y)
    # Use config object for brightness, speed, colors
    # Leverage optimized gamma_correct() and hsv_to_rgb()
    return pixels  # Return modified pixel array
```

### Web Interface

**API Endpoints:**
- `/api/status` - System state and performance metrics
- `/api/config` - Update animation parameters
- `/api/program` - Switch animation programs
- `/api/upload` - Upload custom animation scripts
- **Web UI**: Access at `http://localhost:5001` or `http://192.168.0.222:5001` (Pi)

### Hardware Configuration

**LED Hardware:**
- **WS2811/NeoPixel**: 10x10 matrix (100 LEDs), GPIO12 (Pin 32)
- **HUB75 RGB Panel**: 64x64 matrix (4096 pixels), requires RGB Matrix HAT
- **Hardware PWM**: Solder GPIO4-GPIO18 jumper for HUB75 flicker reduction

**Platform-Specific Settings:**
```bash
# Pi 3B+/4 Performance Optimizations
echo 'isolcpus=3' >> /boot/cmdline.txt           # CPU isolation
echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor  # Performance mode
```

## Current Known Issues

**Animation System Test Failure:**
- `gamma_correct()` signature mismatch causing animation test failures
- **Status**: 6/7 test suites passing, animation system needs signature fix

**Optional Dependencies:**
- `requests` module required for web interface testing
- `psutil` for system monitoring features
- Hardware libraries (`RPi.GPIO`, `rgbmatrix`) for physical hardware

**Active Development:**
- Current action: `optimize-guiand-animations` (10% complete)
- Focus: GUI optimization and animation performance refinement

## Common Development Tasks

**Debugging Commands:**
```bash
# Test current implementation status
python3 test_optimized.py

# Check platform detection and capabilities  
python3 debug_platform.py

# Verify web interface functionality
python3 -c "import requests; print('requests available')" 2>/dev/null || echo "Install: pip install requests"

# Check AICheck status
./aicheck status
```

**Performance Testing:**
```bash
# Run performance benchmarks (after fixes)
pytest tests/benchmarks/performance_benchmarks.py -v

# Monitor real-time performance (with web interface)
curl http://localhost:5001/api/status

# Check system logs
tail -f test_results_optimized.json
```

**Migration and Setup:**
```bash
# Migrate from legacy to optimized (if needed)
python3 scripts/migrate_to_optimized.py

# Quick hardware test (requires sudo)
sudo python3 scripts/matrix_test.py

# Install HUB75 support
sudo bash scripts/install_rgb_matrix.sh
```

## Project Rules

Claude should follow the rules specified in `.aicheck/RULES.md` with focus on documentation-first approach and adherence to language-specific best practices.