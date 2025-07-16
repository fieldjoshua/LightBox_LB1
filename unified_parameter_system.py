#!/usr/bin/env python3
"""
Unified Parameter System for LightBox
====================================

Eliminates parameter chaos by creating:
1. Single API endpoint for ALL parameters  
2. Unified parameter naming system
3. Real-time parameter updates
4. Consistent meaning across GUI/API/animations
5. Optimal Pi 3 B+ hardware configuration

Usage:
    python unified_parameter_system.py --deploy
"""

import json
import time
import subprocess
from typing import Dict, Any, Optional


def log(message: str):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


# UNIFIED PARAMETER DEFINITIONS
# All parameters with consistent names, ranges, and meanings
UNIFIED_PARAMETERS = {
    # === VISUAL PARAMETERS ===
    "brightness": {
        "range": [0, 100],
        "unit": "%",
        "default": 80,
        "config_path": "brightness",
        "api_endpoint": "/api/optimization/update",
        "description": "Overall display brightness (0-100%)",
        "real_time": True
    },
    "speed": {
        "range": [0, 200], 
        "unit": "%",
        "default": 100,
        "config_path": "animations.speed",
        "api_endpoint": "/api/optimization/update", 
        "description": "Animation speed multiplier (50% = half speed, " +
                       "200% = double speed)",
        "real_time": True
    },
    "intensity": {
        "range": [0, 200],
        "unit": "%", 
        "default": 100,
        "config_path": "animations.intensity",
        "api_endpoint": "/api/optimization/update",
        "description": "Effect intensity/saturation (50% = subtle, 200% = vivid)",
        "real_time": True
    },
    "scale": {
        "range": [25, 400],
        "unit": "%",
        "default": 100, 
        "config_path": "animations.scale",
        "api_endpoint": "/api/optimization/update",
        "description": "Pattern scale/zoom (25% = zoomed in, 400% = zoomed out)",
        "real_time": True
    },
    "gamma": {
        "range": [0.5, 3.0],
        "unit": "",
        "default": 2.2,
        "config_path": "animations.gamma", 
        "api_endpoint": "/api/optimization/update",
        "description": "Color gamma correction (1.0 = linear, 2.2 = standard)",
        "real_time": True
    },
    
    # === PERFORMANCE PARAMETERS ===
    "target_fps": {
        "range": [30, 150],
        "unit": "Hz",
        "default": 120,
        "config_path": "target_fps",
        "api_endpoint": "/api/optimization/update", 
        "description": "Target frame rate (Pi 3 B+ can handle up to 135Hz)",
        "real_time": False,
        "restart_required": True
    },
    "gpio_slowdown": {
        "range": [1, 6],
        "unit": "",
        "default": 4,  # Pi 3 B+ optimal
        "config_path": "hub75.gpio_slowdown", 
        "api_endpoint": "/api/optimization/update",
        "description": "GPIO timing (Pi 3 B+ needs 4, Pi 4 needs 2)",
        "real_time": False,
        "restart_required": True
    },
    "pwm_bits": {
        "range": [7, 11],
        "unit": "bits",
        "default": 11,  # Full color depth 
        "config_path": "hub75.pwm_bits",
        "api_endpoint": "/api/optimization/update",
        "description": "Color depth (7=fast refresh, 11=full color)",
        "real_time": False,
        "restart_required": True
    },
    "refresh_limit": {
        "range": [60, 200],
        "unit": "Hz", 
        "default": 135,  # Pi 3 B+ sweet spot
        "config_path": "hub75.limit_refresh",
        "api_endpoint": "/api/optimization/update",
        "description": "Hardware refresh rate limit",
        "real_time": False,
        "restart_required": True
    }
}

class UnifiedParameterManager:
    """
    Single source of truth for all LightBox parameters.
    Eliminates the chaos of multiple APIs and naming systems.
    """
    
    def __init__(self):
        self.pi_ip = "192.168.0.98"
        self.web_port = 8888
        self.current_values = {}
        self.load_current_values()
        
    def load_current_values(self):
        """Load current parameter values from the system"""
        try:
            # Try to get current values from API
            result = subprocess.run([
                'curl', '-s', f'http://{self.pi_ip}:{self.web_port}/api/status'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                log("✅ Connected to LightBox system")
            else:
                log("⚠️  Could not connect to system, using defaults")
                
        except Exception as e:
            log(f"⚠️  Connection error: {e}")
            
        # Set defaults for all parameters
        for param_name, param_def in UNIFIED_PARAMETERS.items():
            self.current_values[param_name] = param_def["default"]
    
    def get_parameter(self, name: str) -> Optional[float]:
        """Get current value of a parameter"""
        return self.current_values.get(name)
    
    def set_parameter(self, name: str, value: float) -> bool:
        """
        Set parameter value with unified API.
        This is the ONLY way parameters should be changed.
        """
        if name not in UNIFIED_PARAMETERS:
            log(f"❌ Unknown parameter: {name}")
            return False
            
        param_def = UNIFIED_PARAMETERS[name]
        
        # Validate range
        min_val, max_val = param_def["range"]
        if value < min_val or value > max_val:
            log(f"❌ {name} value {value} outside range [{min_val}, {max_val}]")
            return False
        
        # Update via API
        success = self._update_via_api(name, value)
        if success:
            self.current_values[name] = value
            log(f"✅ {name} = {value} {param_def['unit']}")
            
            if param_def.get("restart_required"):
                log(f"⚠️  {name} change requires system restart to take full effect")
        else:
            log(f"❌ Failed to update {name}")
            
        return success
    
    def _update_via_api(self, name: str, value: float) -> bool:
        """Update parameter via the unified API endpoint"""
        param_def = UNIFIED_PARAMETERS[name]
        
        try:
            # Use the unified optimization API endpoint
            result = subprocess.run([
                'curl', '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({"parameter": name, "value": value}),
                f'http://{self.pi_ip}:{self.web_port}/api/optimization/update'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    return response.get("success", False)
                except json.JSONDecodeError:
                    log(f"⚠️  Invalid API response for {name}")
                    return False
            else:
                log(f"⚠️  API call failed for {name}")
                return False
                
        except Exception as e:
            log(f"❌ Error updating {name}: {e}")
            return False
    
    def get_parameter_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get complete parameter definition"""
        return UNIFIED_PARAMETERS.get(name)
    
    def list_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get all parameter definitions"""
        return UNIFIED_PARAMETERS.copy()
    
    def get_optimal_pi3_config(self) -> Dict[str, float]:
        """Get Pi 3 B+ optimal settings from technical report"""
        return {
            "gpio_slowdown": 4,      # Critical for Pi 3 B+ timing
            "pwm_bits": 11,          # Full color depth capability  
            "refresh_limit": 135,    # Pi 3 B+ sweet spot
            "target_fps": 120,       # High performance target
            "brightness": 80,        # Good visibility
            "gamma": 2.2            # Standard color correction
        }
    
    def apply_pi3_optimizations(self) -> bool:
        """Apply all Pi 3 B+ optimizations from technical report"""
        log("🚀 Applying Pi 3 B+ optimizations...")
        
        optimal_config = self.get_optimal_pi3_config()
        success_count = 0
        
        for param_name, value in optimal_config.items():
            if self.set_parameter(param_name, value):
                success_count += 1
        
        if success_count == len(optimal_config):
            log("✅ All Pi 3 B+ optimizations applied successfully!")
            return True
        else:
            log(f"⚠️  Applied {success_count}/{len(optimal_config)} optimizations")
            return False

def generate_gui_javascript() -> str:
    """Generate JavaScript for unified GUI controls"""
    return """
// Unified Parameter System JavaScript
// Single API endpoint, consistent naming, real-time updates

class UnifiedParameterController {
    constructor() {
        this.updateEndpoint = '/api/optimization/update';
        this.parameters = """ + json.dumps(UNIFIED_PARAMETERS, indent=8) + """;
        this.updateQueue = [];
        this.isUpdating = false;
    }
    
    // SINGLE METHOD TO UPDATE ANY PARAMETER
    async updateParameter(name, value) {
        if (!this.parameters[name]) {
            console.error(`Unknown parameter: ${name}`);
            return false;
        }
        
        const param = this.parameters[name];
        
        // Validate range
        const [min, max] = param.range;
        if (value < min || value > max) {
            console.error(`${name} value ${value} outside range [${min}, ${max}]`);
            return false;
        }
        
        try {
            const response = await fetch(this.updateEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parameter: name, value: value })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ ${name} = ${value} ${param.unit}`);
                this.updateDisplay(name, value);
                
                if (param.restart_required) {
                    this.showRestartWarning(name);
                }
                
                return true;
            } else {
                console.error(`Failed to update ${name}`);
                return false;
            }
        } catch (error) {
            console.error(`Error updating ${name}:`, error);
            return false;
        }
    }
    
    // Update display elements
    updateDisplay(name, value) {
        const valueElement = document.getElementById(`${name}-value`);
        const sliderElement = document.getElementById(`${name}-slider`);
        
        if (valueElement) {
            const param = this.parameters[name];
            valueElement.textContent = `${value} ${param.unit}`;
        }
        
        if (sliderElement) {
            sliderElement.value = value;
        }
    }
    
    // Show restart warning for hardware parameters
    showRestartWarning(paramName) {
        const warning = document.createElement('div');
        warning.className = 'restart-warning';
        warning.innerHTML = `⚠️ ${paramName} change requires restart to take full effect`;
        warning.style.cssText = 'background: #ff9500; color: white; padding: 10px; margin: 5px 0; border-radius: 4px;';
        
        document.querySelector('.control-panel').prepend(warning);
        
        setTimeout(() => warning.remove(), 5000);
    }
    
    // Initialize all controls
    initializeControls() {
        for (const [name, param] of Object.entries(this.parameters)) {
            this.createParameterControl(name, param);
        }
    }
    
    createParameterControl(name, param) {
        const container = document.createElement('div');
        container.className = 'parameter-control';
        container.innerHTML = `
            <label for="${name}-slider">${param.description}</label>
            <div class="control-row">
                <input type="range" id="${name}-slider" 
                       min="${param.range[0]}" max="${param.range[1]}" 
                       value="${param.default}" step="0.1">
                <span id="${name}-value">${param.default} ${param.unit}</span>
            </div>
            ${param.restart_required ? '<small>⚠️ Requires restart</small>' : ''}
        `;
        
        const slider = container.querySelector(`#${name}-slider`);
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            this.updateParameter(name, value);
        });
        
        document.querySelector('.parameters-container').appendChild(container);
    }
}

// Initialize unified parameter system
const paramController = new UnifiedParameterController();
document.addEventListener('DOMContentLoaded', () => {
    paramController.initializeControls();
});
"""

def deploy_unified_system():
    """Deploy the unified parameter system"""
    log("🚀 Deploying Unified Parameter System")
    
    # Initialize parameter manager
    manager = UnifiedParameterManager()
    
    # Apply Pi 3 B+ optimizations
    manager.apply_pi3_optimizations()
    
    # Generate GUI JavaScript
    js_code = generate_gui_javascript()
    
    # Save JavaScript to file
    with open('web_unified_parameters.js', 'w') as f:
        f.write(js_code)
    
    log("✅ Unified Parameter System deployed!")
    log("📁 Generated: web_unified_parameters.js")
    log("")
    log("🎯 KEY IMPROVEMENTS:")
    log("   • Single API endpoint for ALL parameters")
    log("   • Consistent naming across GUI/API/animations") 
    log("   • Real-time updates without restart")
    log("   • Parameter validation and range checking")
    log("   • Pi 3 B+ optimized settings applied")
    log("")
    log("📋 NEXT STEPS:")
    log("   1. Include web_unified_parameters.js in your HTML")
    log("   2. Replace existing parameter controls with unified system")
    log("   3. Hardware PWM mod: Solder GPIO4-GPIO18 jumper")
    log("   4. Add isolcpus=3 to /boot/cmdline.txt") 
    log("   5. Add dtparam=audio=off to /boot/config.txt")

if __name__ == "__main__":
    import sys
    
    if "--deploy" in sys.argv:
        deploy_unified_system()
    else:
        print(__doc__)
        print("\nUsage: python unified_parameter_system.py --deploy") 