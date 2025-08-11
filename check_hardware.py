#!/usr/bin/env python3
"""
Hardware status check script for LightBox HUB75 setup.
Verifies all critical performance optimizations are in place.
"""

import os
import sys
import subprocess
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_status(status, message):
    """Print status with color."""
    if status == "OK":
        print(f"{GREEN}✓ {message}{RESET}")
    elif status == "WARNING":
        print(f"{YELLOW}⚠ {message}{RESET}")
    elif status == "ERROR":
        print(f"{RED}✗ {message}{RESET}")
    else:
        print(f"  {message}")

def check_platform():
    """Check if running on Raspberry Pi."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM2835' in cpuinfo:
                return "Pi Zero/Zero W"
            elif 'BCM2837' in cpuinfo:
                return "Pi 3B+"
            elif 'BCM2711' in cpuinfo:
                return "Pi 4"
            else:
                return "Unknown Pi"
    except:
        return None

def check_hardware_pwm():
    """Check if GPIO4-GPIO18 jumper is connected."""
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(4, GPIO.OUT)
        GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        GPIO.output(4, GPIO.HIGH)
        import time
        time.sleep(0.001)
        connected = GPIO.input(18) == GPIO.HIGH
        GPIO.output(4, GPIO.LOW)
        
        GPIO.cleanup([4, 18])
        return connected
    except:
        return None

def check_cpu_isolation():
    """Check if CPU isolation is enabled."""
    try:
        with open('/proc/cmdline', 'r') as f:
            cmdline = f.read()
            return 'isolcpus=3' in cmdline
    except:
        return False

def check_audio_disabled():
    """Check if audio is disabled in config.txt."""
    try:
        with open('/boot/config.txt', 'r') as f:
            config = f.read()
            return 'dtparam=audio=off' in config
    except:
        try:
            # Try firmware partition location
            with open('/boot/firmware/config.txt', 'r') as f:
                config = f.read()
                return 'dtparam=audio=off' in config
        except:
            return None

def check_rgbmatrix_library():
    """Check if rgbmatrix library is installed."""
    try:
        import rgbmatrix
        return True
    except ImportError:
        return False

def check_lightbox_config():
    """Check LightBox configuration settings."""
    config_issues = []
    try:
        import json
        config_path = Path(__file__).parent / "config" / "settings.json"
        
        if not config_path.exists():
            return None, ["Configuration file not found"]
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        hub75 = config.get('hub75', {})
        
        # Check critical settings
        if hub75.get('gpio_slowdown', 1) < 4:
            config_issues.append("gpio_slowdown should be 4 for Pi 3B+")
        
        if hub75.get('hardware_mapping') == 'adafruit-hat':
            config_issues.append("hardware_mapping should be 'adafruit-hat-pwm' for hardware PWM")
        
        if not hub75.get('show_refresh_rate', False):
            config_issues.append("show_refresh_rate should be true for performance monitoring")
        
        if hub75.get('pwm_dither_bits', 0) == 0:
            config_issues.append("Consider enabling pwm_dither_bits=1 for smoother colors")
        
        return config, config_issues
    except Exception as e:
        return None, [f"Error reading config: {e}"]

def main():
    """Run all hardware checks."""
    print(f"\n{BOLD}LightBox HUB75 Hardware Status Check{RESET}")
    print("=" * 50)
    
    # Platform check
    print(f"\n{BOLD}Platform Detection:{RESET}")
    platform = check_platform()
    if platform:
        print_status("OK", f"Running on Raspberry {platform}")
    else:
        print_status("WARNING", "Not running on Raspberry Pi - using simulation mode")
    
    # Hardware PWM check
    print(f"\n{BOLD}Hardware PWM Status:{RESET}")
    pwm_status = check_hardware_pwm()
    if pwm_status is True:
        print_status("OK", "GPIO4-GPIO18 jumper detected - hardware PWM enabled!")
    elif pwm_status is False:
        print_status("ERROR", "GPIO4-GPIO18 jumper NOT detected")
        print_status("", "→ Solder a jumper between GPIO4 and GPIO18 for flicker-free display")
    else:
        print_status("WARNING", "Could not check hardware PWM (not on Pi or GPIO not available)")
    
    # CPU isolation check
    print(f"\n{BOLD}CPU Isolation:{RESET}")
    if check_cpu_isolation():
        print_status("OK", "CPU core 3 isolated for matrix updates")
    else:
        print_status("WARNING", "CPU isolation not enabled")
        print_status("", "→ Add 'isolcpus=3' to /boot/cmdline.txt for better performance")
    
    # Audio check
    print(f"\n{BOLD}Audio Configuration:{RESET}")
    audio_status = check_audio_disabled()
    if audio_status is True:
        print_status("OK", "Audio disabled in /boot/config.txt")
    elif audio_status is False:
        print_status("WARNING", "Audio not disabled")
        print_status("", "→ Add 'dtparam=audio=off' to /boot/config.txt")
    else:
        print_status("WARNING", "Could not check audio configuration")
    
    # RGB Matrix library
    print(f"\n{BOLD}RGB Matrix Library:{RESET}")
    if check_rgbmatrix_library():
        print_status("OK", "rgbmatrix library installed")
    else:
        print_status("ERROR", "rgbmatrix library not installed")
        print_status("", "→ Run: sudo bash install_rgb_matrix.sh")
    
    # LightBox configuration
    print(f"\n{BOLD}LightBox Configuration:{RESET}")
    config, issues = check_lightbox_config()
    if config and not issues:
        print_status("OK", "Configuration optimized for performance")
    elif issues:
        for issue in issues:
            print_status("WARNING", issue)
    else:
        print_status("ERROR", "Could not read configuration")
    
    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print("=" * 50)
    
    if platform and pwm_status and check_cpu_isolation() and audio_status and check_rgbmatrix_library() and not issues:
        print(f"{GREEN}{BOLD}✓ All optimizations enabled!{RESET}")
        print("Your LightBox should run at maximum performance.")
    else:
        print(f"{YELLOW}{BOLD}⚠ Some optimizations are missing{RESET}")
        print("Apply the recommended fixes above for better performance.")
    
    print("\nFor more information, see the optimization guide in CLAUDE.md")
    print("")

if __name__ == "__main__":
    main()