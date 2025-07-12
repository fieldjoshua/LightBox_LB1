"""
Unified configuration management with performance optimizations.
Consolidates the best features from all config implementations.
"""

import json
import os
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration with caching and performance optimizations."""
    
    # Default configuration values
    DEFAULTS = {
        "brightness": 0.8,
        "speed": 1.0,
        "color_palette": "rainbow",
        "animation_program": "cosmic",
        "matrix_type": "ws2811",  # ws2811 or hub75
        "target_fps": 30,
        "enable_metrics": True,
        "enable_caching": True,
        
        # WS2811 settings
        "ws2811": {
            "num_pixels": 100,
            "width": 10,
            "height": 10,
            "serpentine": True,
            "data_pin": "D12",
            "gamma": 2.2
        },
        
        # HUB75 settings
        "hub75": {
            "rows": 64,
            "cols": 64,
            "chain_length": 1,
            "parallel": 1,
            "pwm_bits": 11,
            "pwm_lsb_nanoseconds": 130,
            "gpio_slowdown": 4,
            "hardware_pwm": "auto",
            "cpu_isolation": True,
            "limit_refresh": 0,
            "scan_mode": 0,
            "row_address_type": 0,
            "multiplexing": 0
        },
        
        # Performance settings
        "performance": {
            "enable_caching": True,
            "cache_size": 1000,
            "buffer_pool_size": 3,
            "stats_interval": 10,
            "enable_profiling": False
        }
    }
    
    def __init__(self, config_path: str = "settings.json"):
        self.config_path = config_path
        self._config = self._load_config()
        self._dirty = False
        self._lock = threading.Lock()
        
        # Performance optimizations
        self._gamma_table = self._build_gamma_table()
        self._serpentine_map = self._build_serpentine_map()
        self._color_cache = {}  # LRU cache for color conversions
        self._cache_size = self._config.get("performance", {}).get("cache_size", 1000)
        
        # Settings persistence with debouncing
        self._save_timer = None
        self._save_delay = 5.0  # seconds
        
        # Platform detection
        self._platform = self._detect_platform()
        self._apply_platform_defaults()
        
    def _detect_platform(self) -> str:
        """Detect if running on Pi Zero W or Pi 3B+/4."""
        # Check for simulation mode first
        if os.environ.get('LIGHTBOX_SIMULATION') == '1':
            return 'simulation'
            
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM2835' in cpuinfo:  # Pi Zero/Zero W
                    return 'pi_zero_w'
                elif 'BCM2837' in cpuinfo:  # Pi 3B+
                    return 'pi_3b_plus'
                elif 'BCM2711' in cpuinfo:  # Pi 4
                    return 'pi_4'
        except FileNotFoundError:
            # Not on Linux or no cpuinfo
            import platform
            system = platform.system()
            if system == 'Darwin':
                return 'macos_simulation'
            elif system == 'Windows':
                return 'windows_simulation'
            else:
                return 'linux_simulation'
        except:
            pass
        return 'unknown'
    
    def _apply_platform_defaults(self):
        """Apply platform-specific optimizations."""
        if self._platform == 'pi_zero_w':
            # Optimize for Pi Zero W
            if self._config.get("target_fps", 30) > 20:
                self._config["target_fps"] = 20
            self._config["performance"]["enable_profiling"] = False
            logger.info("Applied Pi Zero W optimizations: FPS limited to 20")
            
        elif self._platform in ['pi_3b_plus', 'pi_4']:
            # Enable full optimizations for Pi 3B+/4
            if self._config["matrix_type"] == "hub75":
                self._config["hub75"]["cpu_isolation"] = True
            logger.info(f"Applied {self._platform} optimizations")
            
        elif 'simulation' in self._platform:
            # Simulation mode settings
            self._config["simulation_mode"] = True
            self._config["performance"]["enable_profiling"] = True
            self._config["target_fps"] = 30  # Can handle higher FPS in simulation
            logger.info(f"Running in simulation mode on {self._platform}")
            
        # Mark that platform optimization has been applied
        self._config["platform_optimized"] = True
    
    @property
    def platform(self) -> str:
        """Get detected platform."""
        return self._platform
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults."""
        config = self.DEFAULTS.copy()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    # Deep merge loaded config with defaults
                    self._deep_merge(config, loaded)
                logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            
        return config
    
    def _deep_merge(self, base: dict, updates: dict):
        """Deep merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _build_gamma_table(self) -> List[int]:
        """Pre-calculate gamma correction lookup table for performance."""
        gamma = self._config.get("ws2811", {}).get("gamma", 2.2)
        logger.info(f"Building gamma correction table with gamma={gamma}")
        
        # Pre-calculate all 256 values
        table = []
        for i in range(256):
            corrected = int(255 * pow(i / 255.0, gamma))
            table.append(max(0, min(255, corrected)))
        
        return table
    
    def _build_serpentine_map(self) -> Dict[Tuple[int, int], int]:
        """Pre-calculate serpentine wiring index map."""
        if self._config["matrix_type"] != "ws2811":
            return {}
            
        width = self._config["ws2811"]["width"]
        height = self._config["ws2811"]["height"]
        serpentine = self._config["ws2811"]["serpentine"]
        
        logger.info(f"Building serpentine map for {width}x{height}, serpentine={serpentine}")
        
        mapping = {}
        for y in range(height):
            for x in range(width):
                if serpentine and y % 2 == 1:
                    # Reverse every other row
                    idx = y * width + (width - 1 - x)
                else:
                    idx = y * width + x
                mapping[(x, y)] = idx
                
        return mapping
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with thread safety."""
        with self._lock:
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                value = self._config
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                return value
            return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value with debounced persistence."""
        with self._lock:
            # Handle nested keys
            if '.' in key:
                parts = key.split('.')
                target = self._config
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = value
            else:
                self._config[key] = value
                
            self._dirty = True
            
        # Debounced save
        self._schedule_save()
        
        # Rebuild lookup tables if needed
        if key.startswith("ws2811.gamma"):
            self._gamma_table = self._build_gamma_table()
        elif key.startswith("ws2811.") and any(k in key for k in ["width", "height", "serpentine"]):
            self._serpentine_map = self._build_serpentine_map()
    
    def _schedule_save(self):
        """Schedule a debounced configuration save."""
        if self._save_timer:
            self._save_timer.cancel()
            
        self._save_timer = threading.Timer(self._save_delay, self._save_config)
        self._save_timer.daemon = True
        self._save_timer.start()
    
    def _save_config(self):
        """Save configuration to file."""
        if not self._dirty:
            return
            
        with self._lock:
            try:
                # Create directory if needed
                # Handle case where config_path is just a filename
                dir_path = os.path.dirname(self.config_path) or '.'
                os.makedirs(dir_path, exist_ok=True)
                
                # Write to temp file first
                temp_path = f"{self.config_path}.tmp"
                with open(temp_path, 'w') as f:
                    json.dump(self._config, f, indent=2)
                
                # Atomic rename
                os.replace(temp_path, self.config_path)
                
                self._dirty = False
                logger.info(f"Saved configuration to {self.config_path}")
                
            except Exception as e:
                logger.error(f"Error saving config: {e}")
    
    def xy_to_index(self, x: int, y: int) -> int:
        """Convert x,y coordinates to pixel index using cached map."""
        if self._config["matrix_type"] == "ws2811":
            return self._serpentine_map.get((x, y), 0)
        else:
            # HUB75 uses direct mapping
            width = self._config["hub75"]["cols"]
            return y * width + x
    
    def gamma_correct(self, value: int, color_index: int = 0) -> int:
        """Apply gamma correction using lookup table (fast)."""
        if 0 <= value <= 255:
            return self._gamma_table[value]
        return max(0, min(255, value))
    
    @lru_cache(maxsize=1000)
    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB with caching."""
        # Normalize inputs
        h = h % 1.0
        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))
        
        # Fast HSV to RGB conversion
        c = v * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = v - c
        
        if h < 1/6:
            r, g, b = c, x, 0
        elif h < 2/6:
            r, g, b = x, c, 0
        elif h < 3/6:
            r, g, b = 0, c, x
        elif h < 4/6:
            r, g, b = 0, x, c
        elif h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        # Convert to 8-bit with gamma correction
        r = self.gamma_correct(int((r + m) * 255))
        g = self.gamma_correct(int((g + m) * 255))
        b = self.gamma_correct(int((b + m) * 255))
        
        return (r, g, b)
    
    def get_palette(self, name: str = None) -> List[Tuple[int, int, int]]:
        """Get color palette by name."""
        if name is None:
            name = self._config.get("color_palette", "rainbow")
            
        # Predefined palettes
        palettes = {
            "rainbow": [
                (255, 0, 0),    # Red
                (255, 127, 0),  # Orange
                (255, 255, 0),  # Yellow
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (75, 0, 130),   # Indigo
                (148, 0, 211)   # Violet
            ],
            "fire": [
                (0, 0, 0),      # Black
                (128, 0, 0),    # Dark red
                (255, 0, 0),    # Red
                (255, 128, 0),  # Orange
                (255, 255, 0),  # Yellow
                (255, 255, 128) # Light yellow
            ],
            "ocean": [
                (0, 0, 64),     # Dark blue
                (0, 0, 128),    # Medium blue
                (0, 64, 255),   # Light blue
                (0, 128, 255),  # Cyan blue
                (64, 192, 255), # Light cyan
                (128, 255, 255) # Very light cyan
            ],
            "forest": [
                (0, 32, 0),     # Dark green
                (0, 64, 0),     # Forest green
                (0, 128, 0),    # Green
                (64, 192, 0),   # Light green
                (128, 255, 0),  # Yellow green
                (192, 255, 64)  # Light yellow green
            ]
        }
        
        return palettes.get(name, palettes["rainbow"])
    
    def save_preset(self, name: str):
        """Save current configuration as a preset."""
        preset_dir = "presets"
        os.makedirs(preset_dir, exist_ok=True)
        
        preset_path = os.path.join(preset_dir, f"{name}.json")
        with open(preset_path, 'w') as f:
            json.dump(self._config, f, indent=2)
            
        logger.info(f"Saved preset: {name}")
    
    def load_preset(self, name: str) -> bool:
        """Load configuration from a preset."""
        preset_path = os.path.join("presets", f"{name}.json")
        
        if not os.path.exists(preset_path):
            logger.error(f"Preset not found: {name}")
            return False
            
        try:
            with open(preset_path, 'r') as f:
                preset = json.load(f)
                self._deep_merge(self._config, preset)
                self._dirty = True
                self._schedule_save()
                
                # Rebuild lookup tables
                self._gamma_table = self._build_gamma_table()
                self._serpentine_map = self._build_serpentine_map()
                
                logger.info(f"Loaded preset: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Error loading preset {name}: {e}")
            return False
    
    @property
    def platform(self) -> str:
        """Get detected platform."""
        return self._platform
    
    @property
    def is_pi_zero(self) -> bool:
        """Check if running on Pi Zero W."""
        return self._platform == 'pi_zero_w'
    
    @property
    def supports_hub75(self) -> bool:
        """Check if platform supports HUB75 (Pi 3B+ or better)."""
        return self._platform in ['pi_3b_plus', 'pi_4']
    
    # Compatibility properties for old animation syntax
    @property
    def MATRIX_WIDTH(self) -> int:
        """Compatibility property for old animations."""
        if self._config["matrix_type"] == "ws2811":
            return self._config["ws2811"]["width"]
        else:
            return self._config["hub75"]["cols"]
    
    @property
    def MATRIX_HEIGHT(self) -> int:
        """Compatibility property for old animations."""
        if self._config["matrix_type"] == "ws2811":
            return self._config["ws2811"]["height"]
        else:
            return self._config["hub75"]["rows"]
    
    @property
    def BRIGHTNESS(self) -> float:
        """Compatibility property for old animations."""
        return self._config.get("brightness", 0.8)
    
    @property
    def SPEED(self) -> float:
        """Compatibility property for old animations."""
        return self._config.get("speed", 1.0)
    
    @property
    def SCALE(self) -> float:
        """Compatibility property for old animations."""
        return self._config.get("scale", 1.0)
    
    @property
    def INTENSITY(self) -> float:
        """Compatibility property for old animations."""
        return self._config.get("intensity", 1.0)
    
    @property
    def GAMMA(self) -> float:
        """Compatibility property for old animations."""
        if self._config["matrix_type"] == "ws2811":
            return self._config["ws2811"]["gamma"]
        else:
            return 2.2

    def cleanup(self):
        """Clean up resources."""
        if self._save_timer:
            self._save_timer.cancel()
        self._save_config()  # Final save