"""
Configuration module for LED matrix animations
Provides default settings and palette definitions
"""

import json
import os

class Config:
    """Configuration class for LED animations"""
    
    # LED Hardware Configuration
    LED_COUNT = 100  # 10x10 matrix
    LED_PIN = 12     # GPIO12 (PWM0)
    LED_FREQ_HZ = 800000
    LED_DMA = 10
    LED_INVERT = False
    LED_CHANNEL = 0
    
    # Matrix Configuration
    MATRIX_WIDTH = 10
    MATRIX_HEIGHT = 10
    SERPENTINE = True  # True for zigzag wiring, False for progressive
    
    # Animation Parameters
    BRIGHTNESS = 0.5
    GAMMA = 2.2
    SPEED = 1.0
    SCALE = 1.0
    INTENSITY = 1.0
    
    # Color Palettes
    PALETTES = {
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
            (0, 0, 32),     # Deep blue
            (0, 32, 64),    # Dark blue
            (0, 64, 128),   # Medium blue
            (0, 128, 192),  # Light blue
            (64, 192, 255), # Sky blue
            (128, 255, 255) # Cyan
        ],
        "forest": [
            (0, 32, 0),     # Dark green
            (0, 64, 0),     # Forest green
            (0, 128, 0),    # Green
            (64, 192, 0),   # Light green
            (128, 255, 0),  # Lime
            (192, 255, 64)  # Yellow-green
        ],
        "sunset": [
            (64, 0, 128),   # Purple
            (128, 0, 64),   # Magenta
            (255, 0, 64),   # Pink
            (255, 64, 0),   # Orange
            (255, 128, 0),  # Light orange
            (255, 192, 64)  # Yellow
        ],
        "monochrome": [
            (0, 0, 0),      # Black
            (32, 32, 32),   # Dark gray
            (64, 64, 64),   # Gray
            (128, 128, 128),# Medium gray
            (192, 192, 192),# Light gray
            (255, 255, 255) # White
        ]
    }
    
    # Current palette
    CURRENT_PALETTE = "rainbow"
    
    def __init__(self):
        """Initialize configuration with saved settings if available"""
        self.settings_file = "settings.json"
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    
                # Apply saved settings
                for key, value in settings.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                        
                print(f"Loaded settings from {self.settings_file}")
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings to JSON file"""
        settings = {
            "BRIGHTNESS": self.BRIGHTNESS,
            "GAMMA": self.GAMMA,
            "SPEED": self.SPEED,
            "SCALE": self.SCALE,
            "INTENSITY": self.INTENSITY,
            "CURRENT_PALETTE": self.CURRENT_PALETTE,
            "LED_COUNT": self.LED_COUNT
        }
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"Saved settings to {self.settings_file}")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_palette_colors(self):
        """Get colors from current palette"""
        return self.PALETTES.get(self.CURRENT_PALETTE, self.PALETTES["rainbow"])
    
    def interpolate_palette(self, position):
        """Interpolate color from palette based on position (0.0 - 1.0)"""
        colors = self.get_palette_colors()
        
        if not colors:
            return (0, 0, 0)
        
        # Scale position to palette range
        scaled_pos = position * (len(colors) - 1)
        index = int(scaled_pos)
        fraction = scaled_pos - index
        
        if index >= len(colors) - 1:
            return colors[-1]
        
        # Interpolate between two colors
        color1 = colors[index]
        color2 = colors[index + 1]
        
        r = int(color1[0] * (1 - fraction) + color2[0] * fraction)
        g = int(color1[1] * (1 - fraction) + color2[1] * fraction)
        b = int(color1[2] * (1 - fraction) + color2[2] * fraction)
        
        return (r, g, b)
    
    def xy_to_index(self, x, y):
        """Convert x,y coordinates to LED index for serpentine wiring"""
        if x < 0 or x >= self.MATRIX_WIDTH or y < 0 or y >= self.MATRIX_HEIGHT:
            return None
            
        if self.SERPENTINE:
            # Even rows go left to right, odd rows go right to left
            if y % 2 == 0:
                return y * self.MATRIX_WIDTH + x
            else:
                return y * self.MATRIX_WIDTH + (self.MATRIX_WIDTH - 1 - x)
        else:
            # Progressive wiring - all rows go left to right
            return y * self.MATRIX_WIDTH + x
    
    def index_to_xy(self, index):
        """Convert LED index to x,y coordinates for serpentine wiring"""
        if index < 0 or index >= self.LED_COUNT:
            return None, None
            
        y = index // self.MATRIX_WIDTH
        
        if self.SERPENTINE and y % 2 == 1:
            # Odd rows are reversed
            x = self.MATRIX_WIDTH - 1 - (index % self.MATRIX_WIDTH)
        else:
            x = index % self.MATRIX_WIDTH
            
        return x, y
    
    def to_dict(self):
        """Convert configuration to dictionary"""
        return {
            "brightness": self.BRIGHTNESS,
            "gamma": self.GAMMA,
            "speed": self.SPEED,
            "scale": self.SCALE,
            "intensity": self.INTENSITY,
            "current_palette": self.CURRENT_PALETTE,
            "led_count": self.LED_COUNT,
            "matrix_width": self.MATRIX_WIDTH,
            "matrix_height": self.MATRIX_HEIGHT,
            "serpentine": self.SERPENTINE,
            "palettes": list(self.PALETTES.keys())
        }