/**
 * LightBox Comprehensive Web Interface
 * Handles all configuration, optimization, and control features
 */

class LightBoxController {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.currentConfig = {};
        this.animations = [];
        this.presets = [];
        this.updateInterval = null;
        this.programs = []; // Use 'programs' to be consistent with backend
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabs();
        this.setupWebSocket();
        this.loadInitialData();
        this.startPerformanceUpdates();
    }

    setupEventListeners() {
        // Basic controls
        this.setupSlider('brightness', (value) => this.updateConfig('brightness', value / 100));
        this.setupSlider('speed', (value) => this.updateConfig('speed', value / 100));
        
        // Hardware configuration sliders
        this.setupSlider('target-fps', (value) => this.updateConfig('target_fps', parseInt(value)));
        this.setupSlider('ws2811-gamma', (value) => this.updateConfig('ws2811.gamma', parseFloat(value)));
        this.setupSlider('hue-shift', (value) => this.updateConfig('hue_shift', parseInt(value)));
        this.setupSlider('saturation', (value) => this.updateConfig('saturation', value / 100));
        this.setupSlider('contrast', (value) => this.updateConfig('contrast', value / 100));

        // Selects
        document.getElementById('animation').addEventListener('change', (e) => {
            this.updateConfig('animation_program', e.target.value);
        });

        document.getElementById('palette').addEventListener('change', (e) => {
            this.updateConfig('color_palette', e.target.value);
        });

        // Program selection and switching
        document.getElementById('program-select').addEventListener('change', () => {
            this.loadProgramParameters();
        });

        document.getElementById('switch-program').addEventListener('click', () => {
            const programName = document.getElementById('program-select').value;
            this.switchProgram(programName);
        });

        // Hardware configuration inputs
        this.setupConfigInput('buffer-pool-size', 'performance.buffer_pool_size', 'number');
        this.setupConfigInput('cache-size', 'performance.cache_size', 'number');
        this.setupConfigInput('stats-interval', 'performance.stats_interval', 'number');
        
        this.setupConfigInput('ws2811-pixels', 'ws2811.num_pixels', 'number');
        this.setupConfigInput('ws2811-width', 'ws2811.width', 'number');
        this.setupConfigInput('ws2811-height', 'ws2811.height', 'number');
        this.setupConfigInput('ws2811-pin', 'ws2811.data_pin');
        
        this.setupConfigInput('hub75-rows', 'hub75.rows', 'number');
        this.setupConfigInput('hub75-cols', 'hub75.cols', 'number');
        this.setupConfigInput('hub75-chain', 'hub75.chain_length', 'number');
        this.setupConfigInput('hub75-parallel', 'hub75.parallel', 'number');
        this.setupConfigInput('hub75-pwm-bits', 'hub75.pwm_bits', 'number');
        this.setupConfigInput('hub75-pwm-lsb', 'hub75.pwm_lsb_nanoseconds', 'number');
        this.setupConfigInput('hub75-slowdown', 'hub75.gpio_slowdown', 'number');
        this.setupConfigInput('hub75-scan-mode', 'hub75.scan_mode', 'number');

        // Checkboxes
        this.setupCheckbox('enable-caching', 'performance.enable_caching');
        this.setupCheckbox('enable-profiling', 'performance.enable_profiling');
        this.setupCheckbox('ws2811-serpentine', 'ws2811.serpentine');
        this.setupCheckbox('hub75-hardware-pwm', 'hub75.hardware_pwm');
        this.setupCheckbox('hub75-cpu-isolation', 'hub75.cpu_isolation');

        // Action buttons
        document.getElementById('reset-animation').addEventListener('click', () => this.resetAnimation());
        document.getElementById('clear-cache').addEventListener('click', () => this.clearCache());
        document.getElementById('save-preset').addEventListener('click', () => this.saveCurrentPreset());
        document.getElementById('emergency-stop').addEventListener('click', () => this.emergencyStop());

        // Preset management
        document.getElementById('load-preset').addEventListener('click', () => this.loadSelectedPreset());
        document.getElementById('save-new-preset').addEventListener('click', () => this.saveNewPreset());
        document.getElementById('delete-preset').addEventListener('click', () => this.deleteSelectedPreset());
    }

    setupSlider(id, callback) {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(`${id}-value`);
        
        slider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            let displayValue;
            
            switch(id) {
                case 'brightness':
                case 'saturation':
                case 'contrast':
                    displayValue = `${value}%`;
                    break;
                case 'speed':
                    displayValue = `${(value / 100).toFixed(1)}x`;
                    break;
                case 'hue-shift':
                    displayValue = `${value}°`;
                    break;
                case 'ws2811-gamma':
                    displayValue = value.toFixed(1);
                    break;
                default:
                    displayValue = value.toString();
            }
            
            valueDisplay.textContent = displayValue;
            callback(value);
        });
    }

    setupConfigInput(id, configPath, type = 'text') {
        const input = document.getElementById(id);
        input.addEventListener('change', (e) => {
            let value = e.target.value;
            if (type === 'number') {
                value = parseFloat(value);
            }
            this.updateNestedConfig(configPath, value);
        });
    }

    setupCheckbox(id, configPath) {
        const checkbox = document.getElementById(id);
        checkbox.addEventListener('change', (e) => {
            this.updateNestedConfig(configPath, e.target.checked);
        });
    }

    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));

                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const tabId = tab.dataset.tab;
                document.getElementById(`${tabId}-tab`).classList.add('active');
            });
        });
    }

    setupWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/socket.io/`;
            
            this.ws = io();
            
            this.ws.on('connect', () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            });

            this.ws.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
            });

            this.ws.on('batch_update', (data) => {
                this.handleBatchUpdate(data);
            });

            this.ws.on('status_update', (data) => {
                this.updatePerformanceMetrics(data);
            });

        } catch (error) {
            console.warn('WebSocket not available, falling back to polling');
            this.setupPolling();
        }
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (connected) {
            indicator.style.background = 'var(--success)';
            text.textContent = 'Connected';
        } else {
            indicator.style.background = 'var(--error)';
            text.textContent = 'Disconnected';
        }
    }

    async loadInitialData() {
        try {
            const statusResponse = await fetch('/api/status');
            const status = await statusResponse.json();
            this.programs = status.programs;
            this.currentConfig = status.config;
            this.populateProgramList();
            this.updateUIFromConfig();
            // Presets and other data can be loaded here as before
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    updateUIFromConfig() {
        // Update basic controls
        if (this.currentConfig.brightness !== undefined) {
            const brightness = Math.round(this.currentConfig.brightness * 100);
            document.getElementById('brightness').value = brightness;
            document.getElementById('brightness-value').textContent = `${brightness}%`;
        }

        if (this.currentConfig.speed !== undefined) {
            const speed = Math.round(this.currentConfig.speed * 100);
            document.getElementById('speed').value = speed;
            document.getElementById('speed-value').textContent = `${(speed / 100).toFixed(1)}x`;
        }

        if (this.currentConfig.animation_program) {
            document.getElementById('animation').value = this.currentConfig.animation_program;
        }

        if (this.currentConfig.color_palette) {
            document.getElementById('palette').value = this.currentConfig.color_palette;
        }

        // Update target FPS
        if (this.currentConfig.target_fps !== undefined) {
            document.getElementById('target-fps').value = this.currentConfig.target_fps;
            document.getElementById('target-fps-value').textContent = this.currentConfig.target_fps.toString();
        }
    }

    populateProgramList() {
        const select = document.getElementById('program-select');
        select.innerHTML = '';
        this.programs.forEach(program => {
            const option = document.createElement('option');
            option.value = program;
            option.textContent = program.charAt(0).toUpperCase() + program.slice(1);
            select.appendChild(option);
        });
        // Set the current program as selected
        if (this.currentConfig.current_program) {
            select.value = this.currentConfig.current_program;
        }
        this.loadProgramParameters(); // Load params for the selected program
    }

    async loadProgramParameters() {
        const programName = document.getElementById('program-select').value;
        if (!programName) return;

        try {
            const response = await fetch(`/api/program-parameters/${programName}`);
            const data = await response.json();
            this.renderParameters(data.parameters);
        } catch (error) {
            console.error(`Error loading parameters for ${programName}:`, error);
        }
    }

    renderParameters(parameters) {
        const container = document.getElementById('program-parameters-container');
        container.innerHTML = ''; // Clear existing controls
        
        for (const key in parameters) {
            const param = parameters[key];
            const controlGroup = document.createElement('div');
            controlGroup.className = 'control-group';

            const label = document.createElement('label');
            label.setAttribute('for', key);
            label.textContent = param.description || key;
            
            let input;
            // Create sliders, inputs, etc. based on param.type
            if (param.type === 'range') {
                input = document.createElement('input');
                input.type = 'range';
                input.min = param.min || 0;
                input.max = param.max || 100;
                input.step = param.step || 1;
                input.value = param.value || param.default;
            } else { // Default to text input
                input = document.createElement('input');
                input.type = 'text';
                input.value = param.value || param.default;
            }
            input.id = key;

            controlGroup.appendChild(label);
            controlGroup.appendChild(input);
            container.appendChild(controlGroup);
            
            // Add event listener to update parameter on change
            input.addEventListener('change', (e) => {
                this.updateProgramParameter(programName, key, e.target.value);
            });
        }
    }

    updateSystemInfo(status) {
        document.getElementById('platform').textContent = status.platform || '--';
        document.getElementById('matrix-type').textContent = status.matrix_type || '--';
        document.getElementById('resolution').textContent = 
            status.resolution ? `${status.resolution.width}x${status.resolution.height}` : '--';
    }

    startPerformanceUpdates() {
        this.updateInterval = setInterval(() => {
            this.fetchPerformanceData();
        }, 2000);
    }

    async fetchPerformanceData() {
        try {
            const response = await fetch('/api/performance');
            const data = await response.json();
            this.updatePerformanceMetrics(data);
        } catch (error) {
            console.error('Error fetching performance data:', error);
        }
    }

    updatePerformanceMetrics(data) {
        // Update FPS
        if (data.fps) {
            document.getElementById('fps').textContent = data.fps.current?.toFixed(1) || '--';
            this.updatePerformanceBar('fps-bar', data.fps.current, 60);
        }

        // Update CPU
        if (data.cpu_percent) {
            document.getElementById('cpu').textContent = `${data.cpu_percent.current?.toFixed(1) || '--'}%`;
            this.updatePerformanceBar('cpu-bar', data.cpu_percent.current, 100);
        }

        // Update Memory
        if (data.memory_mb) {
            document.getElementById('memory').textContent = `${data.memory_mb.current?.toFixed(0) || '--'} MB`;
            this.updatePerformanceBar('memory-bar', data.memory_mb.current, 512);
        }

        // Update Frame Time
        if (data.frame_time_ms) {
            document.getElementById('frame-time').textContent = `${data.frame_time_ms.current?.toFixed(1) || '--'} ms`;
        }

        // Update dropped frames
        if (data.dropped_frames_percent) {
            const dropped = data.dropped_frames_percent.current || 0;
            document.getElementById('dropped').textContent = `${dropped.toFixed(1)}%`;
        }

        // Update cache hit rate
        if (data.cache_hit_rate) {
            const hitRate = data.cache_hit_rate.current || 0;
            document.getElementById('cache-hit').textContent = `${hitRate.toFixed(1)}%`;
        }
    }

    updatePerformanceBar(barId, value, max) {
        const bar = document.getElementById(barId);
        if (!bar || value === undefined) return;

        const percentage = Math.min((value / max) * 100, 100);
        bar.style.width = `${percentage}%`;

        // Color coding
        if (percentage < 50) {
            bar.style.background = 'var(--success)';
        } else if (percentage < 80) {
            bar.style.background = 'var(--warning)';
        } else {
            bar.style.background = 'var(--error)';
        }
    }

    async updateConfig(key, value) {
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ [key]: value }),
            });

            if (response.ok) {
                this.currentConfig[key] = value;
            } else {
                console.error('Failed to update config:', await response.text());
            }
        } catch (error) {
            console.error('Error updating config:', error);
        }
    }

    updateNestedConfig(path, value) {
        const keys = path.split('.');
        const data = {};
        let current = data;

        for (let i = 0; i < keys.length - 1; i++) {
            current[keys[i]] = {};
            current = current[keys[i]];
        }
        current[keys[keys.length - 1]] = value;

        this.updateConfig(keys[0], keys.length === 1 ? value : data[keys[0]]);
    }

    async updateAnimationParam(param, value) {
        try {
            const response = await fetch('/api/animation/param', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ param, value }),
            });

            if (!response.ok) {
                console.error('Failed to update animation param:', await response.text());
            }
        } catch (error) {
            console.error('Error updating animation param:', error);
        }
    }

    async resetAnimation() {
        try {
            const response = await fetch('/api/animation/reset', { method: 'POST' });
            if (response.ok) {
                console.log('Animation reset successfully');
            }
        } catch (error) {
            console.error('Error resetting animation:', error);
        }
    }

    async clearCache() {
        try {
            const response = await fetch('/api/cache/clear', { method: 'POST' });
            if (response.ok) {
                console.log('Cache cleared successfully');
            }
        } catch (error) {
            console.error('Error clearing cache:', error);
        }
    }

    async saveCurrentPreset() {
        const name = prompt('Enter preset name:');
        if (name) {
            try {
                const response = await fetch(`/api/preset/${name}`, { method: 'POST' });
                if (response.ok) {
                    console.log('Preset saved successfully');
                    await this.loadInitialData(); // Refresh preset list
                }
            } catch (error) {
                console.error('Error saving preset:', error);
            }
        }
    }

    async saveNewPreset() {
        const name = document.getElementById('preset-name').value.trim();
        if (!name) {
            alert('Please enter a preset name');
            return;
        }

        try {
            const response = await fetch(`/api/preset/${name}`, { method: 'POST' });
            if (response.ok) {
                console.log('Preset saved successfully');
                document.getElementById('preset-name').value = '';
                await this.loadInitialData(); // Refresh preset list
            }
        } catch (error) {
            console.error('Error saving preset:', error);
        }
    }

    async loadSelectedPreset() {
        const presetName = document.getElementById('preset-list').value;
        if (!presetName) {
            alert('Please select a preset to load');
            return;
        }

        try {
            const response = await fetch(`/api/preset/${presetName}`, { method: 'GET' });
            if (response.ok) {
                console.log('Preset loaded successfully');
                await this.loadInitialData(); // Refresh UI
            }
        } catch (error) {
            console.error('Error loading preset:', error);
        }
    }

    async deleteSelectedPreset() {
        const presetName = document.getElementById('preset-list').value;
        if (!presetName) {
            alert('Please select a preset to delete');
            return;
        }

        if (confirm(`Are you sure you want to delete preset "${presetName}"?`)) {
            try {
                const response = await fetch(`/api/preset/${presetName}`, { method: 'DELETE' });
                if (response.ok) {
                    console.log('Preset deleted successfully');
                    await this.loadInitialData(); // Refresh preset list
                }
            } catch (error) {
                console.error('Error deleting preset:', error);
            }
        }
    }

    async emergencyStop() {
        if (confirm('Emergency stop will immediately halt all animations. Continue?')) {
            try {
                const response = await fetch('/api/emergency-stop', { method: 'POST' });
                if (response.ok) {
                    console.log('Emergency stop activated');
                }
            } catch (error) {
                console.error('Error during emergency stop:', error);
            }
        }
    }

    async switchProgram(programName) {
        try {
            await fetch('/api/program', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ program: programName })
            });
        } catch (error) {
            console.error('Error switching program:', error);
        }
    }

    handleBatchUpdate(data) {
        data.updates.forEach(([event, updateData]) => {
            switch (event) {
                case 'config_update':
                    Object.assign(this.currentConfig, updateData);
                    this.updateUIFromConfig();
                    break;
                case 'performance_update':
                    this.updatePerformanceMetrics(updateData);
                    break;
                default:
                    console.log('Unknown update event:', event);
            }
        });
    }

    setupPolling() {
        // Fallback polling if WebSocket is not available
        setInterval(() => {
            this.fetchPerformanceData();
        }, 5000);
    }
}

// Initialize the controller
document.addEventListener('DOMContentLoaded', () => {
    new LightBoxController();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.lightboxController && window.lightboxController.updateInterval) {
        clearInterval(window.lightboxController.updateInterval);
    }
});