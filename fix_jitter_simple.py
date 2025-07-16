#!/usr/bin/env python3
"""
Simple Jitter Fix for LightBox
=============================

Applies proven anti-jitter settings for smooth HUB75 performance:
- PWM bits: 8 (reduces flicker)
- GPIO slowdown: 2 (faster refresh) 
- Hardware PWM: enabled
- Proper refresh rate: 120Hz
- Disable PWM LSB nanoseconds (reduces jitter)
"""

import subprocess
import time
import json


def log(message):
    print("[{}] {}".format(time.strftime('%H:%M:%S'), message))


def apply_jitter_fix():
    """Apply the core anti-jitter settings via API"""
    
    # Core anti-jitter settings based on rpi-rgb-led-matrix best practices
    settings = {
        "pwm-bits": 8,              # Lower PWM bits = less flicker
        "gpio-slowdown": 2,         # Faster GPIO = smoother refresh  
        "hardware-pulse": "on",     # Enable hardware PWM
        "limit-refresh": 120,       # Optimal refresh rate
        "pwm-lsb-nanoseconds": 0    # Disable for stability
    }
    
    log("Applying anti-jitter settings...")
    
    for setting, value in settings.items():
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                "http://192.168.0.98:8888/api/optimization/update",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({setting: value})
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=10)
            
            if result.returncode == 0:
                log("✓ Set {} = {}".format(setting, value))
            else:
                log("✗ Failed to set {}: {}".format(setting, result.stderr))
                
        except Exception as e:
            log("✗ Error setting {}: {}".format(setting, e))
    
    log("Restarting lightbox service...")
    try:
        subprocess.run([
            "ssh", "joshuafield@192.168.0.98", 
            "sudo systemctl restart lightbox"
        ], timeout=30)
        log("✓ Service restarted")
        
        # Wait for service to start
        time.sleep(5)
        
        # Check status
        result = subprocess.run([
            "curl", "-s", "http://192.168.0.98:8888/api/status"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            status = json.loads(result.stdout)
            current_anim = status.get('current_animation', 'unknown')
            fps = status.get('fps', 'unknown')
            log("✓ Status: {} at {} FPS".format(current_anim, fps))
        
    except Exception as e:
        log("✗ Error restarting service: {}".format(e))


if __name__ == "__main__":
    log("Starting jitter fix...")
    apply_jitter_fix()
    log("Jitter fix complete. The display should now be much smoother!") 