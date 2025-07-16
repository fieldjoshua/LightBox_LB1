"""
Enhanced Configuration Manager for LightBox
Supports nested keys, type conversion, and persistent storage
"""

import os
import json
import math
import platform
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Union, cast

logger = logging.getLogger(__name__)


class ConfigManager:
    """Enhanced configuration manager with dot notation access and persistence."""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """Initialize configuration with path to settings file."""
        self.config_path = config_path
        self.config = {}
        
        # Default color palette
        self.palettes = {
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
            ]
        }
        self.current_palette = "rainbow"
        
        # Initialize configurations
        self.load_config()
        self._build_gamma_table()
        self._build_serpentine_map()
        self._serpentine_map = {}  # Initialize serpentine map attribute
        
        # Detect platform
        self.platform = self._detect_platform()
        logger.info(f"Running in {self.platform}")
    
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        system = platform.system().lower()
        
        if "linux" in system:
            # Check if we're running on Raspberry Pi
            try:
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().strip("\0")
                    if "raspberry pi" in model.lower():
                        return "raspberry_pi"
            except:
                pass
            
            return "linux"
        elif "darwin" in system:
            return "macos_simulation"
        elif "windows" in system:
            return "windows_simulation"
        else:
            return "unknown"
    
    def _build_gamma_table(self):
        """Build gamma correction lookup table."""
        gamma = self.get("gamma", 2.2)
        self._gamma_table = [min(255, int((i / 255.0) ** gamma * 255 + 0.5)) 
                          for i in range(256)]
        logger.info(f"Building gamma correction table with gamma={gamma}")
    
    def _build_serpentine_map(self):
        """Build serpentine pixel mapping for matrix."""
        width = self.get("matrix_width", 10)
        height = self.get("matrix_height", 10)
        serpentine = self.get("serpentine", True)
        
        logger.info(f"Building serpentine map for {width}x{height}, serpentine={serpentine}")
        
        # Initialize map
        self.pixel_map = [0] * (width * height)
        
        for y in range(height):
            for x in range(width):
                # Calculate target index
                if serpentine and y % 2 == 1:
                    # Reverse every other row for serpentine
                    idx = y * width + (width - 1 - x)
                else:
                    # Regular mapping
                    idx = y * width + x
                
                # Store physical position to index
                if idx < len(self.pixel_map):
                    self.pixel_map[idx] = y * width + x
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            # Resolve path to support both absolute and relative paths
            path = Path(self.config_path).expanduser()
            
            if not path.exists():
                logger.warning(f"Configuration file not found: {path}")
                return False
            
            with open(path, 'r') as f:
                self.config = json.load(f)
            
            # Update current palette
            if "palettes" in self.config:
                self.palettes.update(self.config["palettes"])
                if "current" in self.config["palettes"]:
                    self.current_palette = self.config["palettes"]["current"]
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file."""
        try:
            # Make sure directory exists
            path = Path(self.config_path).expanduser()
            path.parent.mkdir(exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value, supporting dot notation for nested keys."""
        # Handle nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            current = self.config
            
            for part in parts[:-1]:
                if part not in current:
                    return default
                current = current[part]
            
            last_part = parts[-1]
            return current.get(last_part, default)
        
        # Simple key
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value, supporting dot notation for nested keys."""
        # Handle nested keys with dot notation
        if "." in key:
            parts = key.split(".")
            current = self.config
            
            # Navigate to the right nesting level
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[parts[-1]] = value
            
        else:
            # Simple key
            self.config[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Return the entire configuration dictionary."""
        return self.config
    
    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """
        Convert HSV color to RGB.
        
        Args:
            h (float): Hue in range [0.0, 1.0]
            s (float): Saturation in range [0.0, 1.0]
            v (float): Value in range [0.0, 1.0]
            
        Returns:
            Tuple[int, int, int]: RGB values in range [0, 1]
        """
        h = max(0.0, min(1.0, h))
        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))
        
        if s == 0.0:
            # Achromatic (gray)
            return (v, v, v)
        
        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i % 6 == 0:
            return (v, t, p)
        elif i % 6 == 1:
            return (q, v, p)
        elif i % 6 == 2:
            return (p, v, t)
        elif i % 6 == 3:
            return (p, q, v)
        elif i % 6 == 4:
            return (t, p, v)
        else:
            return (v, p, q)
    
    def gamma_correct(self, value: float, gamma: Optional[float] = None) -> float:
        """Apply gamma correction to a value."""
        if gamma is None:
            # Use precomputed table for integer values
            if 0 <= value <= 1:
                return self._gamma_table[int(value * 255)] / 255.0
            else:
                return value
        
        # Custom gamma value
        return value ** (1.0 / gamma)
    
    def xy_to_index(self, x: int, y: int) -> Optional[int]:
        """Convert x,y coordinates to LED index, respecting serpentine wiring."""
        width = self.get("matrix_width", 10)
        height = self.get("matrix_height", 10)
        
        # Check bounds
        if x < 0 or y < 0 or x >= width or y >= height:
            return None
            
        # Calculate linear index
        index = y * width + x
            
        # Apply mapping if available
        if hasattr(self, 'pixel_map') and 0 <= index < len(self.pixel_map):
            return self.pixel_map[index]
        
        return index
    
    def index_to_xy(self, index: int) -> Optional[Tuple[int, int]]:
        """Convert LED index to x,y coordinates."""
        width = self.get("matrix_width", 10)
        height = self.get("matrix_height", 10)
        
        if index < 0 or index >= width * height:
            return None
        
        # Get logical index from physical index
        logical_index = index
        if hasattr(self, 'pixel_map'):
            # Find the logical index that maps to this physical index
            # This is an expensive operation but rarely used
            try:
                logical_index = self.pixel_map.index(index)
            except ValueError:
                # If not found, use the original index
                logical_index = index
        
        # Convert to x,y
        x = logical_index % width
        y = logical_index // width
        
        return (x, y)
    
    def get_palette_colors(self) -> List[Tuple[int, int, int]]:
        """Get current palette colors."""
        palette_name = self.current_palette
        if palette_name not in self.palettes:
            palette_name = "rainbow"  # Default fallback
            
        return self.palettes[palette_name]
    
    def interpolate_palette(self, position: float) -> Tuple[int, int, int]:
        """Interpolate color from current palette based on position (0.0 - 1.0)."""
        colors = self.get_palette_colors()
        
        if not colors:
            return (0, 0, 0)
        
        # Wrap position to [0, 1)
        position = position % 1.0
        
        # Scale position to palette range
        scaled_pos = position * (len(colors) - 1)
        index = int(scaled_pos)
        fraction = scaled_pos - index
        
        # Handle edge case
        if index >= len(colors) - 1:
            return colors[-1]
        
        # Interpolate between two colors
        color1 = colors[index]
        color2 = colors[index + 1]
        
        r = color1[0] * (1 - fraction) + color2[0] * fraction
        g = color1[1] * (1 - fraction) + color2[1] * fraction
        b = color1[2] * (1 - fraction) + color2[2] * fraction
        
        return (int(r), int(g), int(b))