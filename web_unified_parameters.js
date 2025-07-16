
// Unified Parameter System JavaScript
// Single API endpoint, consistent naming, real-time updates

class UnifiedParameterController {
    constructor() {
        this.updateEndpoint = '/api/optimization/update';
        this.parameters = {
        "brightness": {
                "range": [
                        0,
                        100
                ],
                "unit": "%",
                "default": 80,
                "config_path": "brightness",
                "api_endpoint": "/api/optimization/update",
                "description": "Overall display brightness (0-100%)",
                "real_time": true
        },
        "speed": {
                "range": [
                        0,
                        200
                ],
                "unit": "%",
                "default": 100,
                "config_path": "animations.speed",
                "api_endpoint": "/api/optimization/update",
                "description": "Animation speed multiplier (50% = half speed, 200% = double speed)",
                "real_time": true
        },
        "intensity": {
                "range": [
                        0,
                        200
                ],
                "unit": "%",
                "default": 100,
                "config_path": "animations.intensity",
                "api_endpoint": "/api/optimization/update",
                "description": "Effect intensity/saturation (50% = subtle, 200% = vivid)",
                "real_time": true
        },
        "scale": {
                "range": [
                        25,
                        400
                ],
                "unit": "%",
                "default": 100,
                "config_path": "animations.scale",
                "api_endpoint": "/api/optimization/update",
                "description": "Pattern scale/zoom (25% = zoomed in, 400% = zoomed out)",
                "real_time": true
        },
        "gamma": {
                "range": [
                        0.5,
                        3.0
                ],
                "unit": "",
                "default": 2.2,
                "config_path": "animations.gamma",
                "api_endpoint": "/api/optimization/update",
                "description": "Color gamma correction (1.0 = linear, 2.2 = standard)",
                "real_time": true
        },
        "target_fps": {
                "range": [
                        30,
                        150
                ],
                "unit": "Hz",
                "default": 120,
                "config_path": "target_fps",
                "api_endpoint": "/api/optimization/update",
                "description": "Target frame rate (Pi 3 B+ can handle up to 135Hz)",
                "real_time": false,
                "restart_required": true
        },
        "gpio_slowdown": {
                "range": [
                        1,
                        6
                ],
                "unit": "",
                "default": 4,
                "config_path": "hub75.gpio_slowdown",
                "api_endpoint": "/api/optimization/update",
                "description": "GPIO timing (Pi 3 B+ needs 4, Pi 4 needs 2)",
                "real_time": false,
                "restart_required": true
        },
        "pwm_bits": {
                "range": [
                        7,
                        11
                ],
                "unit": "bits",
                "default": 11,
                "config_path": "hub75.pwm_bits",
                "api_endpoint": "/api/optimization/update",
                "description": "Color depth (7=fast refresh, 11=full color)",
                "real_time": false,
                "restart_required": true
        },
        "refresh_limit": {
                "range": [
                        60,
                        200
                ],
                "unit": "Hz",
                "default": 135,
                "config_path": "hub75.limit_refresh",
                "api_endpoint": "/api/optimization/update",
                "description": "Hardware refresh rate limit",
                "real_time": false,
                "restart_required": true
        }
};
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
