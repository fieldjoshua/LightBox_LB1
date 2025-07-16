/**
 * LightBox HUB75 Comprehensive Control
 * Advanced JavaScript for comprehensive web control panel with WebSocket support
 */

// Global state
let socket;
let config = {};
let animations = [];
let currentAnimation = "";
let presets = {};
let performanceData = {
    fps: 0,
    frameCount: 0,
    refreshRate: 0,
    cpuUsage: 0,
    memory: 0,
    uptime: 0
};
let hwPwmDetected = false;
let cpuIsolationDetected = false;

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    fetchInitialData();
    setupEventListeners();
});

// Initialize WebSocket connection for real-time updates
function initializeWebSocket() {
    try {
        // Get the current host from the browser URL
        const host = window.location.hostname;
        const port = window.location.port;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        
        // Connect to Socket.IO endpoint
        socket = io(`${wsProtocol}://${host}:${port}`, {
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000
        });

        // Socket event handlers
        socket.on('connect', () => {
            updateConnectionStatus(true);
            console.log('WebSocket connected');
        });

        socket.on('disconnect', () => {
            updateConnectionStatus(false);
            console.log('WebSocket disconnected');
        });

        socket.on('connect_error', (error) => {
            updateConnectionStatus(false);
            console.error('WebSocket connection error:', error);
        });

        // Listen for real-time updates
        socket.on('performance_update', (data) => {
            updatePerformanceMetrics(data);
        });

        socket.on('status_update', (data) => {
            updateStatusDisplay(data);
        });

        socket.on('config_update', (data) => {
            updateConfig(data);
        });

        socket.on('hardware_status', (data) => {
            updateHardwareStatus(data);
        });

        // Handle batch updates
        socket.on('batch_update', (data) => {
            for (const update of data.updates) {
                const [event, payload] = update;
                handleBatchUpdate(event, payload);
            }
        });
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus(false);
    }
}

// Handle batched updates from server
function handleBatchUpdate(event, payload) {
    switch (event) {
        case 'performance_update':
            updatePerformanceMetrics(payload);
            break;
        case 'status_update':
            updateStatusDisplay(payload);
            break;
        case 'config_update':
            updateConfig(payload);
            break;
        case 'hardware_status':
            updateHardwareStatus(payload);
            break;
        default:
            console.log(`Unhandled event type: ${event}`);
    }
}

// Fetch initial data from server
async function fetchInitialData() {
    try {
        // Fetch configuration
        const configResponse = await fetch('/api/hardware/config');
        if (configResponse.ok) {
            config = await configResponse.json();
            updateUIFromConfig(config);
        }

        // Fetch animations list
        const animationsResponse = await fetch('/api/animations');
        if (animationsResponse.ok) {
            const animData = await animationsResponse.json();
            animations = animData.animations || [];
            populateAnimationSelector(animations);
        }

        // Fetch palettes
        const palettesResponse = await fetch('/api/palettes');
        if (palettesResponse.ok) {
            const paletteData = await palettesResponse.json();
            populatePaletteSelector(paletteData.palettes);
        }

        // Fetch presets
        const presetsResponse = await fetch('/api/presets');
        if (presetsResponse.ok) {
            presets = await presetsResponse.json();
            populatePresetsList(presets);
        }

        // Fetch system info
        const systemResponse = await fetch('/api/system/info');
        if (systemResponse.ok) {
            const systemInfo = await systemResponse.json();
            updateSystemInfo(systemInfo);
        }
    } catch (error) {
        console.error('Failed to fetch initial data:', error);
    }
}

// Update UI with config values
function updateUIFromConfig(config) {
    // Display configuration
    if (config.hub75) {
        document.getElementById('matrix-rows').value = config.hub75.rows || 64;
        document.getElementById('matrix-cols').value = config.hub75.cols || 64;
        document.getElementById('chain-length').value = config.hub75.chain_length || 1;
        document.getElementById('parallel').value = config.hub75.parallel || 1;
        
        // Select the hardware mapping
        const mappingSelect = document.getElementById('hardware-mapping');
        if (mappingSelect) {
            mappingSelect.value = config.hub75.hardware_mapping || 'adafruit-hat';
        }
        
        // Panel configuration
        document.getElementById('scan-mode').value = config.hub75.scan_mode || 0;
        document.getElementById('row-address-type').value = config.hub75.row_address_type || 0;
        document.getElementById('multiplexing').value = config.hub75.multiplexing || 0;
        
        // PWM configuration
        const pwmBits = document.getElementById('pwm-bits');
        if (pwmBits) {
            pwmBits.value = config.hub75.pwm_bits || 11;
            document.getElementById('pwm-bits-value').textContent = pwmBits.value;
        }
        
        const pwmLsb = document.getElementById('pwm-lsb-ns');
        if (pwmLsb) {
            pwmLsb.value = config.hub75.pwm_lsb_nanoseconds || 130;
            document.getElementById('pwm-lsb-ns-value').textContent = pwmLsb.value;
        }
        
        const pwmDither = document.getElementById('pwm-dither-bits');
        if (pwmDither) {
            pwmDither.value = config.hub75.pwm_dither_bits || 0;
            document.getElementById('pwm-dither-bits-value').textContent = pwmDither.value;
        }
        
        // Hardware PWM
        document.getElementById('hardware-pwm').value = config.hub75.hardware_pwm || 'auto';
        document.getElementById('hardware-pwm-mod').checked = 
            config.hardware && config.hardware.hardware_pwm_mod;
            
        // Performance settings
        const gpioSlowdown = document.getElementById('gpio-slowdown');
        if (gpioSlowdown) {
            gpioSlowdown.value = config.hub75.gpio_slowdown || 4;
            document.getElementById('gpio-slowdown-value').textContent = gpioSlowdown.value;
        }
        
        const limitRefresh = document.getElementById('limit-refresh');
        if (limitRefresh) {
            limitRefresh.value = config.hub75.limit_refresh || 120;
            document.getElementById('limit-refresh-value').textContent = 
                limitRefresh.value > 0 ? `${limitRefresh.value} Hz` : 'Unlimited';
        }
    }
    
    // Target FPS
    const targetFps = document.getElementById('target-fps');
    if (targetFps) {
        targetFps.value = config.target_fps || 30;
        document.getElementById('target-fps-value').textContent = targetFps.value;
    }
    
    // Performance settings
    if (config.performance) {
        document.getElementById('cpu-isolation').checked = 
            config.performance.cpu_isolation !== undefined ? config.performance.cpu_isolation : true;
        document.getElementById('double-buffering').checked = 
            config.performance.use_double_buffering !== undefined ? config.performance.use_double_buffering : true;
        document.getElementById('show-refresh-rate').checked = 
            config.hub75 && config.hub75.show_refresh_rate;
        document.getElementById('fixed-frame-time').checked = 
            config.performance.fixed_frame_time !== undefined ? config.performance.fixed_frame_time : true;
    }
    
    // System settings
    if (config.system) {
        document.getElementById('log-level').value = config.system.log_level || 'INFO';
        document.getElementById('auto-save-presets').checked = 
            config.system.auto_save_presets !== undefined ? config.system.auto_save_presets : true;
        document.getElementById('headless-mode').checked = 
            config.system.headless_mode !== undefined ? config.system.headless_mode : true;
        document.getElementById('os-optimization').checked = 
            config.system.os_optimization !== undefined ? config.system.os_optimization : true;
    }
    
    // Hardware components
    if (config.hardware) {
        document.getElementById('buttons-enabled').checked = 
            config.hardware.buttons_enabled !== undefined ? config.hardware.buttons_enabled : true;
        document.getElementById('oled-enabled').checked = 
            config.hardware.oled_enabled !== undefined ? config.hardware.oled_enabled : true;
    }
    
    // Animation controls
    document.getElementById('brightness').value = config.brightness || 0.8;
    document.getElementById('brightness-value').textContent = `${Math.round((config.brightness || 0.8) * 100)}%`;
    
    document.getElementById('speed').value = config.animations ? (config.animations.speed || 1.0) : 1.0;
    document.getElementById('speed-value').textContent = `${document.getElementById('speed').value}x`;
    
    document.getElementById('intensity').value = config.animations ? (config.animations.intensity || 1.0) : 1.0;
    document.getElementById('intensity-value').textContent = `${document.getElementById('intensity').value}x`;
    
    document.getElementById('scale').value = config.animations ? (config.animations.scale || 1.0) : 1.0;
    document.getElementById('scale-value').textContent = `${document.getElementById('scale').value}x`;
}

// Populate animation selector
function populateAnimationSelector(animations) {
    const select = document.getElementById('animation-select');
    if (!select) return;
    
    select.innerHTML = '';
    
    animations.forEach(anim => {
        const option = document.createElement('option');
        option.value = anim.name || anim;
        option.textContent = formatAnimationName(anim.name || anim);
        select.appendChild(option);
        
        // Set as selected if it's the current animation
        if (anim.name === currentAnimation || anim === currentAnimation) {
            option.selected = true;
        }
    });
    
    // Load animation parameters for the current selection
    loadAnimationParameters(select.value);
}

// Format animation name for display (convert snake_case or camelCase to Title Case)
function formatAnimationName(name) {
    return name
        .replace(/([a-z])([A-Z])/g, '$1 $2') // Convert camelCase to spaces
        .replace(/_/g, ' ')                   // Convert snake_case to spaces
        .replace(/^\w/, c => c.toUpperCase()) // Capitalize first letter
        .replace(/\b\w/g, l => l.toUpperCase()); // Capitalize each word
}

// Populate palette selector
function populatePaletteSelector(palettes) {
    const select = document.getElementById('palette');
    if (!select) return;
    
    select.innerHTML = '';
    
    palettes.forEach(palette => {
        const option = document.createElement('option');
        option.value = palette.name || palette;
        option.textContent = formatAnimationName(palette.name || palette);
        select.appendChild(option);
        
        // Set as selected if it's the current palette
        if (config.palettes && palette === config.palettes.current) {
            option.selected = true;
            updatePalettePreview(palette);
        }
    });
}

// Update palette preview
function updatePalettePreview(paletteName) {
    const preview = document.getElementById('palette-preview');
    if (!preview || !config.palettes || !config.palettes[paletteName]) return;
    
    const colors = config.palettes[paletteName];
    if (!Array.isArray(colors)) return;
    
    // Create a gradient CSS string
    const stops = colors.map((color, index) => {
        const percent = (index / (colors.length - 1)) * 100;
        const [r, g, b] = color;
        return `rgb(${r}, ${g}, ${b}) ${percent}%`;
    }).join(', ');
    
    preview.style.background = `linear-gradient(90deg, ${stops})`;
}

// Populate presets list
function populatePresetsList(presets) {
    const list = document.getElementById('presets-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    Object.entries(presets).forEach(([name, preset]) => {
        const presetDiv = document.createElement('div');
        presetDiv.className = 'control-group';
        
        const presetName = document.createElement('div');
        presetName.textContent = name;
        presetName.style.marginBottom = '8px';
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.style.display = 'flex';
        buttonsDiv.style.gap = '8px';
        
        const loadButton = document.createElement('button');
        loadButton.textContent = 'Load';
        loadButton.onclick = () => loadPreset(name);
        
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.className = 'danger';
        deleteButton.onclick = () => deletePreset(name);
        
        buttonsDiv.appendChild(loadButton);
        buttonsDiv.appendChild(deleteButton);
        
        presetDiv.appendChild(presetName);
        presetDiv.appendChild(buttonsDiv);
        
        list.appendChild(presetDiv);
    });
}

// Load animation parameters
function loadAnimationParameters(animationName) {
    fetch(`/api/animation/${animationName}/params`)
        .then(response => response.json())
        .then(params => {
            const container = document.getElementById('animation-params');
            if (!container) return;
            
            container.innerHTML = '';
            
            if (!params || Object.keys(params).length === 0) {
                container.innerHTML = '<p>No adjustable parameters for this animation.</p>';
                return;
            }
            
            Object.entries(params).forEach(([param, value]) => {
                const paramType = typeof value;
                const group = document.createElement('div');
                group.className = 'control-group';
                
                const label = document.createElement('label');
                label.textContent = formatAnimationName(param);
                group.appendChild(label);
                
                if (paramType === 'number') {
                    const row = document.createElement('div');
                    row.className = 'control-row';
                    
                    const input = document.createElement('input');
                    input.type = 'range';
                    input.id = `param-${param}`;
                    input.min = value / 10;
                    input.max = value * 10;
                    input.step = value / 20;
                    input.value = value;
                    
                    const valueDisplay = document.createElement('span');
                    valueDisplay.id = `param-${param}-value`;
                    valueDisplay.textContent = value;
                    
                    input.oninput = () => {
                        valueDisplay.textContent = input.value;
                        updateAnimationParameter(animationName, param, parseFloat(input.value));
                    };
                    
                    row.appendChild(input);
                    row.appendChild(valueDisplay);
                    group.appendChild(row);
                } else if (paramType === 'boolean') {
                    const checkboxGroup = document.createElement('div');
                    checkboxGroup.className = 'checkbox-group';
                    
                    const input = document.createElement('input');
                    input.type = 'checkbox';
                    input.id = `param-${param}`;
                    input.checked = value;
                    
                    input.onchange = () => {
                        updateAnimationParameter(animationName, param, input.checked);
                    };
                    
                    checkboxGroup.appendChild(input);
                    
                    const checkboxLabel = document.createElement('label');
                    checkboxLabel.textContent = formatAnimationName(param);
                    checkboxLabel.setAttribute('for', `param-${param}`);
                    checkboxGroup.appendChild(checkboxLabel);
                    
                    group.appendChild(checkboxGroup);
                } else if (Array.isArray(value)) {
                    const select = document.createElement('select');
                    select.id = `param-${param}`;
                    
                    value.forEach(option => {
                        const opt = document.createElement('option');
                        opt.value = option;
                        opt.textContent = option;
                        select.appendChild(opt);
                    });
                    
                    select.onchange = () => {
                        updateAnimationParameter(animationName, param, select.value);
                    };
                    
                    group.appendChild(select);
                }
                
                container.appendChild(group);
            });
        })
        .catch(error => {
            console.error('Failed to load animation parameters:', error);
        });
}

// Update animation parameter
function updateAnimationParameter(animation, param, value) {
    fetch('/api/animation/param', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            animation,
            param,
            value
        })
    })
    .catch(error => {
        console.error('Failed to update animation parameter:', error);
    });
}

// Update connection status display
function updateConnectionStatus(connected) {
    const statusSpan = document.getElementById('connection-status');
    if (!statusSpan) return;
    
    if (connected) {
        statusSpan.textContent = 'Connected';
        statusSpan.className = 'status-good';
    } else {
        statusSpan.textContent = 'Disconnected';
        statusSpan.className = 'status-error';
    }
}

// Update performance metrics display
function updatePerformanceMetrics(data) {
    performanceData = { ...performanceData, ...data };
    
    // Update FPS and refresh rate
    document.getElementById('metric-fps').textContent = data.fps.toFixed(1);
    document.getElementById('fps').textContent = data.fps.toFixed(1);
    document.getElementById('metric-refresh-rate').textContent = `${data.refresh_rate.toFixed(1)} Hz`;
    document.getElementById('refresh-rate').textContent = data.refresh_rate.toFixed(1);
    
    // Update other metrics
    document.getElementById('metric-frame-count').textContent = data.frame_count;
    document.getElementById('metric-cpu').textContent = `${data.cpu_usage.toFixed(1)}%`;
    document.getElementById('metric-memory').textContent = `${(data.memory_usage / 1024 / 1024).toFixed(1)} MB`;
    
    // Format uptime as HH:MM:SS
    const hours = Math.floor(data.uptime / 3600);
    const minutes = Math.floor((data.uptime % 3600) / 60);
    const seconds = Math.floor(data.uptime % 60);
    const formattedUptime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('metric-uptime').textContent = formattedUptime;
}

// Update status display with animation and config info
function updateStatusDisplay(data) {
    if (data.current_animation) {
        currentAnimation = data.current_animation;
        
        // Update animation selector
        const animationSelect = document.getElementById('animation-select');
        if (animationSelect) {
            for (let i = 0; i < animationSelect.options.length; i++) {
                if (animationSelect.options[i].value === currentAnimation) {
                    animationSelect.selectedIndex = i;
                    break;
                }
            }
        }
    }
    
    // Update brightness and speed
    if (data.brightness !== undefined) {
        const brightnessSlider = document.getElementById('brightness');
        if (brightnessSlider) {
            brightnessSlider.value = data.brightness;
            document.getElementById('brightness-value').textContent = `${Math.round(data.brightness * 100)}%`;
        }
    }
    
    if (data.speed !== undefined) {
        const speedSlider = document.getElementById('speed');
        if (speedSlider) {
            speedSlider.value = data.speed;
            document.getElementById('speed-value').textContent = `${data.speed}x`;
        }
    }
    
    // Update palette
    if (data.palette) {
        const paletteSelect = document.getElementById('palette');
        if (paletteSelect) {
            for (let i = 0; i < paletteSelect.options.length; i++) {
                if (paletteSelect.options[i].value === data.palette) {
                    paletteSelect.selectedIndex = i;
                    updatePalettePreview(data.palette);
                    break;
                }
            }
        }
    }
}

// Update hardware status indicators
function updateHardwareStatus(data) {
    if (data.hardware_pwm !== undefined) {
        hwPwmDetected = data.hardware_pwm;
        const hwPwmStatus = document.getElementById('hardware-pwm-status-value');
        if (hwPwmStatus) {
            hwPwmStatus.textContent = hwPwmDetected ? 'Detected' : 'Not Detected';
            hwPwmStatus.className = hwPwmDetected ? 'status-good' : 'status-warning';
        }
    }
    
    if (data.cpu_isolation !== undefined) {
        cpuIsolationDetected = data.cpu_isolation;
        const cpuIsolationStatus = document.getElementById('cpu-isolation-status-value');
        if (cpuIsolationStatus) {
            cpuIsolationStatus.textContent = cpuIsolationDetected ? 'Enabled' : 'Not Detected';
            cpuIsolationStatus.className = cpuIsolationDetected ? 'status-good' : 'status-warning';
        }
    }
    
    // Update system info
    if (data.system) {
        updateSystemInfo(data.system);
    }
}

// Update system information display
function updateSystemInfo(info) {
    if (info.pi_model) {
        document.getElementById('pi-model').textContent = info.pi_model;
    }
    
    if (info.software_version) {
        document.getElementById('software-version').textContent = info.software_version;
    }
    
    if (info.driver_version) {
        document.getElementById('driver-version').textContent = info.driver_version;
    }
    
    if (info.network_status) {
        document.getElementById('network-status').textContent = info.network_status;
    }
}

// Update config object with new values
function updateConfig(data) {
    config = { ...config, ...data };
    updateUIFromConfig(config);
}

// Load a preset
function loadPreset(name) {
    fetch(`/api/preset/${name}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log(`Loaded preset: ${name}`);
    })
    .catch(error => {
        console.error(`Failed to load preset ${name}:`, error);
    });
}

// Delete a preset
function deletePreset(name) {
    if (!confirm(`Are you sure you want to delete preset "${name}"?`)) {
        return;
    }
    
    fetch(`/api/preset/${name}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        console.log(`Deleted preset: ${name}`);
        fetchInitialData(); // Refresh preset list
    })
    .catch(error => {
        console.error(`Failed to delete preset ${name}:`, error);
    });
}

// Save current config as a preset
function savePreset(name) {
    fetch('/api/preset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            config: {
                animation_program: currentAnimation,
                brightness: parseFloat(document.getElementById('brightness').value),
                speed: parseFloat(document.getElementById('speed').value),
                intensity: parseFloat(document.getElementById('intensity').value),
                scale: parseFloat(document.getElementById('scale').value),
                palette: document.getElementById('palette').value
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(`Saved preset: ${name}`);
        fetchInitialData(); // Refresh preset list
    })
    .catch(error => {
        console.error(`Failed to save preset ${name}:`, error);
    });
}

// Set up event listeners
function setupEventListeners() {
    // Animation controls
    document.getElementById('btn-apply-animation').addEventListener('click', () => {
        const animation = document.getElementById('animation-select').value;
        fetch('/api/animation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ animation })
        })
        .then(() => {
            currentAnimation = animation;
            loadAnimationParameters(animation);
        })
        .catch(error => {
            console.error('Failed to set animation:', error);
        });
    });
    
    document.getElementById('btn-reset-animation').addEventListener('click', () => {
        fetch('/api/animation/reset', {
            method: 'POST'
        })
        .then(() => {
            loadAnimationParameters(currentAnimation);
        })
        .catch(error => {
            console.error('Failed to reset animation:', error);
        });
    });
    
    // Brightness control
    document.getElementById('brightness').addEventListener('change', () => {
        const brightness = parseFloat(document.getElementById('brightness').value);
        fetch('/api/brightness', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ brightness })
        })
        .catch(error => {
            console.error('Failed to set brightness:', error);
        });
    });
    
    // Speed control
    document.getElementById('speed').addEventListener('change', () => {
        const speed = parseFloat(document.getElementById('speed').value);
        fetch('/api/speed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ speed })
        })
        .catch(error => {
            console.error('Failed to set speed:', error);
        });
    });
    
    // Palette selector
    document.getElementById('palette').addEventListener('change', () => {
        const palette = document.getElementById('palette').value;
        fetch('/api/palette', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ palette })
        })
        .then(() => {
            updatePalettePreview(palette);
        })
        .catch(error => {
            console.error('Failed to set palette:', error);
        });
    });
    
    // Save preset
    document.getElementById('btn-save-preset').addEventListener('click', () => {
        const name = prompt('Enter preset name:');
        if (name) {
            savePreset(name);
        }
    });
    
    // Create preset
    const createPresetBtn = document.getElementById('btn-create-preset');
    if (createPresetBtn) {
        createPresetBtn.addEventListener('click', () => {
            const name = document.getElementById('new-preset-name').value;
            if (name) {
                savePreset(name);
                document.getElementById('new-preset-name').value = '';
            } else {
                alert('Please enter a preset name');
            }
        });
    }
    
    // System actions
    document.getElementById('btn-clear-cache').addEventListener('click', () => {
        fetch('/api/cache/clear', {
            method: 'POST'
        })
        .then(() => {
            alert('Cache cleared successfully');
        })
        .catch(error => {
            console.error('Failed to clear cache:', error);
        });
    });
    
    document.getElementById('btn-optimize').addEventListener('click', () => {
        fetch('/api/system/optimize', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(`System optimized: ${data.message}`);
        })
        .catch(error => {
            console.error('Failed to optimize system:', error);
        });
    });
    
    document.getElementById('btn-emergency-stop').addEventListener('click', () => {
        if (confirm('Are you sure you want to perform an emergency stop?')) {
            fetch('/api/emergency-stop', {
                method: 'POST'
            })
            .catch(error => {
                console.error('Failed to perform emergency stop:', error);
            });
        }
    });
    
    // Restart system
    const restartBtn = document.getElementById('btn-restart');
    if (restartBtn) {
        restartBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to restart the system?')) {
                fetch('/api/system/restart', {
                    method: 'POST'
                })
                .catch(error => {
                    console.error('Failed to restart system:', error);
                });
            }
        });
    }
    
    // Animation select change
    const animationSelect = document.getElementById('animation-select');
    if (animationSelect) {
        animationSelect.addEventListener('change', () => {
            loadAnimationParameters(animationSelect.value);
        });
    }
}