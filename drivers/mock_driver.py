"""
Mock driver for development on non-Raspberry Pi systems.
This driver simulates a matrix display for testing and development.
"""

import logging
import time
from typing import Tuple, List, Union
from .matrix_driver import MatrixDriver

logger = logging.getLogger(__name__)


class MockDriver(MatrixDriver):
    """Mock driver for development and testing."""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get matrix configuration
        if config.get("matrix_type") == "hub75":
            hub_config = config.get("hub75", {})
            self.width = hub_config.get("cols", 64)
            self.height = hub_config.get("rows", 64)
        else:
            self.width = 64
            self.height = 64
            
        self.num_pixels = self.width * self.height
        self._brightness = config.get("brightness", 0.8)
        self.frame_buffer = [(0, 0, 0)] * self.num_pixels
        self.frame_count = 0
        self.start_time = time.time()
        
        logger.info(f"Mock driver initialized with {self.width}x{self.height} resolution")
    
    def initialize(self) -> bool:
        """Initialize the mock driver."""
        logger.info("Mock driver initialized")
        return True
    
    def update(self, frame_buffer: Union[List[Tuple[int, int, int]], bytearray]) -> None:
        """Update the mock display with new pixel data."""
        self.frame_buffer = list(frame_buffer)
        self.frame_count += 1
        
        # Simulate some processing time
        time.sleep(1.0 / 60.0)  # 60fps simulation
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a single pixel in the buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            index = y * self.width + x
            self.frame_buffer[index] = (r, g, b)
    
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill the entire display with a single color."""
        self.frame_buffer = [(r, g, b)] * self.num_pixels
    
    def clear(self) -> None:
        """Clear the display to black."""
        self.frame_buffer = [(0, 0, 0)] * self.num_pixels
    
    def show(self) -> None:
        """Update the display with the current buffer."""
        # In a real driver this would push to hardware
        pass
    
    @property
    def brightness(self) -> float:
        """Get current brightness level."""
        return self._brightness
    
    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set brightness level."""
        self._brightness = max(0.0, min(1.0, value))
    
    def set_brightness(self, brightness: float) -> None:
        """Set the brightness level (0.0 to 1.0)."""
        self._brightness = max(0.0, min(1.0, brightness))
        logger.debug(f"Mock brightness set to {self._brightness}")
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int] = (255, 255, 255)) -> int:
        """Draw text at the specified position (simulated)."""
        logger.debug(f"Mock text: '{text}' at ({x}, {y})")
        return x + len(text) * 6  # Simulate text width
    
    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]):
        """Draw a line between two points (simulated)."""
        logger.debug(f"Mock line: ({x0}, {y0}) to ({x1}, {y1})")
    
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """Draw a circle (simulated)."""
        logger.debug(f"Mock circle: center ({x}, {y}), radius {radius}")
    
    def get_hardware_status(self) -> dict:
        """Get hardware status information."""
        return {
            "type": "mock",
            "resolution": f"{self.width}x{self.height}",
            "brightness": self._brightness,
            "frame_count": self.frame_count,
            "uptime": time.time() - self.start_time,
            "fps": self.frame_count / max(1, time.time() - self.start_time),
            "hardware_pwm": False,
            "cpu_isolation": False,
            "temperature": 25.0  # Mock temperature
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Mock driver cleaned up") 