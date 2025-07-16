#!/usr/bin/env python3
"""
Hardware detection utilities for Raspberry Pi LED matrix.
Provides functions for detecting hardware PWM and CPU isolation.
"""

import os
import time
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - hardware detection will be limited")

# GPIO pins for hardware PWM detection
GPIO_PWM_OUT = 4   # GPIO4 output pin
GPIO_PWM_IN = 18   # GPIO18 input pin (must be connected to GPIO4 for hardware PWM)


def detect_hardware_pwm():
    """
    Detect if hardware PWM is available by testing GPIO4-GPIO18 jumper.
    
    The hardware PWM jumper connects GPIO4 to GPIO18, enabling hardware
    pulse generation instead of software PWM. This eliminates flicker
    and horizontal line artifacts common with software PWM.
    
    Returns:
        bool: True if hardware PWM jumper is detected, False otherwise
    """
    if not GPIO_AVAILABLE:
        # Try alternative detection using file check
        return _detect_hardware_pwm_alt()
        
    try:
        # Save current GPIO state
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configure pins
        GPIO.setup(GPIO_PWM_OUT, GPIO.OUT)
        GPIO.setup(GPIO_PWM_IN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Test connection in both states to verify reliable connection
        # First test HIGH
        GPIO.output(GPIO_PWM_OUT, GPIO.HIGH)
        time.sleep(0.001)  # Ensure signal propagation
        high_state = GPIO.input(GPIO_PWM_IN) == GPIO.HIGH
        
        # Then test LOW
        GPIO.output(GPIO_PWM_OUT, GPIO.LOW)
        time.sleep(0.001)  # Ensure signal propagation
        low_state = GPIO.input(GPIO_PWM_IN) == GPIO.LOW
        
        # Cleanup
        GPIO.cleanup([GPIO_PWM_OUT, GPIO_PWM_IN])
        
        # Both tests must pass for reliable hardware PWM
        connected = high_state and low_state
        
        logger.info(f"Hardware PWM detection: {'DETECTED' if connected else 'NOT DETECTED'}")
        return connected
        
    except Exception as e:
        logger.debug(f"Hardware PWM detection error: {e}")
        # Fallback to alternative detection
        return _detect_hardware_pwm_alt()


def _detect_hardware_pwm_alt():
    """
    Alternative hardware PWM detection using file system or Pi model checks.
    Used when RPi.GPIO is not available.
    
    Returns:
        bool: True if hardware PWM might be enabled, False otherwise
    """
    try:
        # Check for hardware PWM flag file that might have been manually created
        pwm_flag_file = Path("/boot/pwm_enabled")
        if pwm_flag_file.exists():
            return True
            
        # Check boot config for PWM-related settings
        boot_config = Path("/boot/config.txt")
        if boot_config.exists():
            with open(boot_config, 'r') as f:
                config_content = f.read()
                if "dtoverlay=pwm" in config_content:
                    return True
        
        return False
    except Exception as e:
        logger.debug(f"Alternative PWM detection error: {e}")
        return False


def check_cpu_isolation():
    """
    Check if CPU isolation is enabled (isolcpus=3).
    
    CPU isolation reserves a dedicated core for the LED matrix update thread,
    preventing system processes from interrupting the display refresh.
    This significantly improves performance and reduces flicker on
    multi-core Raspberry Pi models (3B+, 4).
    
    Returns:
        bool: True if CPU isolation is enabled, False otherwise
    """
    try:
        # Check kernel command line for isolcpus parameter
        cmdline_path = Path("/proc/cmdline")
        if cmdline_path.exists():
            with open(cmdline_path, 'r') as f:
                cmdline = f.read()
                # Check for isolcpus=3 or isolcpus=2,3 or similar
                if 'isolcpus=' in cmdline:
                    # Parse the isolcpus parameter to check if core 3 is isolated
                    for param in cmdline.split():
                        if param.startswith('isolcpus='):
                            # Extract the value after 'isolcpus='
                            cores = param.split('=')[1].split(',')
                            # Check if core 3 is in the list
                            if '3' in cores:
                                logger.info("CPU isolation detected: Core 3 is isolated")
                                return True
        
        logger.info("CPU isolation not detected")
        return False
    except Exception as e:
        logger.debug(f"CPU isolation check error: {e}")
        return False


def get_raspberry_pi_model():
    """
    Get the Raspberry Pi model information.
    
    Returns:
        str: The Raspberry Pi model string or "Unknown" if not available
    """
    try:
        model_path = Path("/proc/device-tree/model")
        if model_path.exists():
            with open(model_path, 'r') as f:
                return f.read().strip('\0')
        
        # Alternative method using vcgencmd
        try:
            result = subprocess.run(
                ['vcgencmd', 'get_config', 'int'],
                capture_output=True, 
                text=True, 
                check=True
            )
            if 'arm_freq=' in result.stdout:
                return "Raspberry Pi (unknown model)"
        except:
            pass
            
        return "Unknown"
    except Exception:
        return "Unknown"


def get_system_info():
    """
    Get detailed system information.
    
    Returns:
        dict: Dictionary containing system information
    """
    info = {
        'model': get_raspberry_pi_model(),
        'hardware_pwm': detect_hardware_pwm(),
        'cpu_isolation': check_cpu_isolation(),
    }
    
    # Try to get CPU temperature
    try:
        temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
        if temp_path.exists():
            with open(temp_path, 'r') as f:
                temp_milliC = int(f.read().strip())
                info['cpu_temperature'] = temp_milliC / 1000.0
    except:
        pass
    
    # Try to get memory information
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    info['memory_total'] = int(line.split()[1]) / 1024  # MB
                elif line.startswith('MemAvailable:'):
                    info['memory_available'] = int(line.split()[1]) / 1024  # MB
                    break
    except:
        pass
    
    # Try to get kernel version
    try:
        result = subprocess.run(['uname', '-r'], capture_output=True, text=True, check=True)
        info['kernel_version'] = result.stdout.strip()
    except:
        pass
        
    return info


if __name__ == "__main__":
    """
    Run as a standalone script to test hardware detection.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test hardware detection
    print("=== Raspberry Pi Hardware Detection ===")
    
    model = get_raspberry_pi_model()
    print(f"Model: {model}")
    
    hardware_pwm = detect_hardware_pwm()
    print(f"Hardware PWM: {'Detected' if hardware_pwm else 'Not detected'}")
    
    cpu_isolation = check_cpu_isolation()
    print(f"CPU Isolation: {'Enabled' if cpu_isolation else 'Not enabled'}")
    
    # Get full system info
    print("\n=== System Information ===")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        if key not in ['model', 'hardware_pwm', 'cpu_isolation']:
            print(f"{key}: {value}") 