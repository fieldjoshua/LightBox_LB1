// LightBox Control Panel JavaScript

class LightBoxControl {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.updateInterval = null;
        
        // Cache DOM elements
        this.elements = {
            status: document.querySelector('.status'),
            statusText: document.querySelector('.status-text'),
            fps: document.getElementById('fps'),
            cpu: document.getElementById('cpu'),
            memory: document.getElementById('memory'),
            dropped: document.getElementById('dropped'),
            brightness: document.getElementById('brightness'),
            brightnessValue: document.getElementById('brightness-value'),
            speed: document.getElementById('speed'),
            speedValue: document.getElementById('speed-value'),
            animation: document.getElementById('animation'),
            palette: document.getElementById('palette'),
            presetList: document.getElementById('preset-list'),
            loadPreset: document.getElementById('load-preset'),
            savePreset: document.getElementById('save-preset'),
            deletePreset: document.getElementById('delete-preset'),
            matrixType: document.getElementById('matrix-type'),
            platform: document.getElementById('platform'),
            targetFps: document.getElementById('target-fps')
        };
        
        this.init();
    }
    
    init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Try to connect WebSocket
        this.connectWebSocket();
        
        // Load initial data
        this.loadAnimations();
        this.loadPresets();
        this.loadStatus();
        
        // Start periodic updates
        this.startUpdates();
    }
    
    setupEventListeners() {
        // Brightness control
        this.elements.brightness.addEventListener('input', (e) => {
            const value = e.target.value;
            this.elements.brightnessValue.textContent = `${value}%`;
            this.updateConfig({ brightness: value / 100 });
        });
        
        // Speed control
        this.elements.speed.addEventListener('input', (e) => {
            const value = e.target.value / 100;
            this.elements.speedValue.textContent = `${value.toFixed(1)}x`;
            this.updateConfig({ speed: value });
        });
        
        // Animation selection
        this.elements.animation.addEventListener('change', (e) => {
            this.updateConfig({ animation_program: e.target.value });
        });
        
        // Palette selection
        this.elements.palette.addEventListener('change', (e) => {
            this.updateConfig({ color_palette: e.target.value });
        });
        
        // Preset controls
        this.elements.loadPreset.addEventListener('click', () => this.loadPreset());
        this.elements.savePreset.addEventListener('click', () => this.savePreset());
        this.elements.deletePreset.addEventListener('click', () => this.deletePreset());
    }
    
    connectWebSocket() {
        // Check if Socket.IO is available
        if (typeof io === 'undefined') {
            console.log('Socket.IO not available, using polling only');
            return;
        }
        
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.connected = true;
                this.updateConnectionStatus(true);
                console.log('WebSocket connected');
            });
            
            this.socket.on('disconnect', () => {
                this.connected = false;
                this.updateConnectionStatus(false);
                console.log('WebSocket disconnected');
            });
            
            this.socket.on('status_update', (data) => {
                this.updateDisplay(data);
            });
            
            this.socket.on('batch_update', (data) => {
                // Process batched updates
                data.updates.forEach(([event, value]) => {
                    this.handleUpdate(event, value);
                });
            });
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.elements.status.classList.add('connected');
            this.elements.status.classList.remove('disconnected');
            this.elements.statusText.textContent = 'Connected';
        } else {
            this.elements.status.classList.remove('connected');
            this.elements.status.classList.add('disconnected');
            this.elements.statusText.textContent = 'Disconnected';
        }
    }
    
    async loadAnimations() {
        try {
            const response = await fetch('/api/animations');
            const animations = await response.json();
            
            this.elements.animation.innerHTML = '';
            animations.forEach(anim => {
                const option = document.createElement('option');
                option.value = anim.name;
                option.textContent = anim.name.charAt(0).toUpperCase() + anim.name.slice(1);
                this.elements.animation.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load animations:', error);
        }
    }
    
    async loadPresets() {
        try {
            const response = await fetch('/api/presets');
            const presets = await response.json();
            
            this.elements.presetList.innerHTML = '<option value="">Select preset...</option>';
            presets.forEach(preset => {
                const option = document.createElement('option');
                option.value = preset;
                option.textContent = preset;
                this.elements.presetList.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load presets:', error);
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            this.updateDisplay(status);
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }
    
    updateDisplay(status) {
        // Update performance metrics
        if (status.performance) {
            const perf = status.performance;
            this.elements.fps.textContent = perf.fps.current.toFixed(1);
            this.elements.cpu.textContent = perf.cpu_percent.current.toFixed(1) + '%';
            this.elements.memory.textContent = perf.memory_mb.current.toFixed(1) + ' MB';
            this.elements.dropped.textContent = perf.drop_rate.toFixed(1) + '%';
        }
        
        // Update controls
        if (status.brightness !== undefined) {
            this.elements.brightness.value = status.brightness * 100;
            this.elements.brightnessValue.textContent = `${Math.round(status.brightness * 100)}%`;
        }
        
        if (status.speed !== undefined) {
            this.elements.speed.value = status.speed * 100;
            this.elements.speedValue.textContent = `${status.speed.toFixed(1)}x`;
        }
        
        if (status.animation) {
            this.elements.animation.value = status.animation;
        }
        
        if (status.palette) {
            this.elements.palette.value = status.palette;
        }
        
        // Update system info
        if (status.matrix_type) {
            this.elements.matrixType.textContent = status.matrix_type.toUpperCase();
        }
        
        if (status.platform) {
            this.elements.platform.textContent = status.platform.replace(/_/g, ' ').toUpperCase();
        }
        
        if (status.performance && status.performance.fps) {
            this.elements.targetFps.textContent = status.performance.fps.average.toFixed(0);
        }
    }
    
    async updateConfig(config) {
        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                throw new Error('Failed to update configuration');
            }
        } catch (error) {
            console.error('Failed to update config:', error);
        }
    }
    
    handleUpdate(event, value) {
        switch (event) {
            case 'brightness':
                this.elements.brightness.value = value * 100;
                this.elements.brightnessValue.textContent = `${Math.round(value * 100)}%`;
                break;
            case 'speed':
                this.elements.speed.value = value * 100;
                this.elements.speedValue.textContent = `${value.toFixed(1)}x`;
                break;
            case 'animation':
                this.elements.animation.value = value;
                break;
            case 'palette':
                this.elements.palette.value = value;
                break;
        }
    }
    
    async loadPreset() {
        const presetName = this.elements.presetList.value;
        if (!presetName) return;
        
        try {
            const response = await fetch(`/api/preset/${presetName}`);
            if (response.ok) {
                // Reload status to update all controls
                await this.loadStatus();
                alert(`Preset "${presetName}" loaded successfully`);
            }
        } catch (error) {
            console.error('Failed to load preset:', error);
            alert('Failed to load preset');
        }
    }
    
    async savePreset() {
        const presetName = prompt('Enter preset name:');
        if (!presetName) return;
        
        try {
            const response = await fetch(`/api/preset/${presetName}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                await this.loadPresets();
                alert(`Preset "${presetName}" saved successfully`);
            }
        } catch (error) {
            console.error('Failed to save preset:', error);
            alert('Failed to save preset');
        }
    }
    
    async deletePreset() {
        const presetName = this.elements.presetList.value;
        if (!presetName) return;
        
        if (!confirm(`Delete preset "${presetName}"?`)) return;
        
        try {
            const response = await fetch(`/api/preset/${presetName}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await this.loadPresets();
                alert(`Preset "${presetName}" deleted`);
            }
        } catch (error) {
            console.error('Failed to delete preset:', error);
            alert('Failed to delete preset');
        }
    }
    
    startUpdates() {
        // Update performance metrics every 2 seconds
        this.updateInterval = setInterval(() => {
            if (!this.connected) {
                // Use polling if WebSocket not connected
                this.loadStatus();
            }
        }, 2000);
    }
    
    stopUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LightBoxControl();
});