"""
Optimized WS2811/NeoPixel driver with double buffering and performance improvements.
"""

import logging
from typing import Tuple, List, Union
from .matrix_driver import MatrixDriver

logger = logging.getLogger(__name__)

try:
    import board
    import neopixel
    NEOPIXEL_AVAILABLE = True
except ImportError:
    NEOPIXEL_AVAILABLE = False
    logger.warning("NeoPixel library not available")


class WS2811Driver(MatrixDriver):
    """Optimized WS2811/NeoPixel driver with double buffering."""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get WS2811 configuration
        ws_config = config.get("ws2811", {})
        self.width = ws_config.get("width", 10)
        self.height = ws_config.get("height", 10)
        self.num_pixels = ws_config.get("num_pixels", 100)
        self.serpentine = ws_config.get("serpentine", True)
        self.data_pin = ws_config.get("data_pin", "D12")
        
        # Performance optimizations
        self.gamma_table = config._gamma_table  # Use pre-calculated gamma
        self.serpentine_map = config._serpentine_map  # Use pre-calculated mapping
        
        # Double buffering
        self._back_buffer = [(0, 0, 0)] * self.num_pixels
        self._front_buffer = None  # Will be the NeoPixel object
        
        # Brightness
        self._brightness = config.get("brightness", 0.8)
        
        logger.info(f"WS2811 driver configured: {self.width}x{self.height}, "
                   f"serpentine={self.serpentine}, pin={self.data_pin}")
    
    def initialize(self) -> bool:
        """Initialize the NeoPixel hardware."""
        if not NEOPIXEL_AVAILABLE:
            logger.error("NeoPixel library not available")
            return False
            
        try:
            # Map pin name to board pin
            pin = getattr(board, self.data_pin.replace("D", "D"))
            
            # Create NeoPixel object with auto_write disabled for better performance
            self._front_buffer = neopixel.NeoPixel(
                pin,
                self.num_pixels,
                brightness=self._brightness,
                auto_write=False,  # Important for performance
                pixel_order=neopixel.GRB
            )
            
            # Initialize to black
            self._front_buffer.fill((0, 0, 0))
            self._front_buffer.show()
            
            logger.info("WS2811 hardware initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WS2811: {e}")
            return False
    
    def update(self, frame_buffer: Union[List[Tuple[int, int, int]], bytearray]) -> None:
        """Update with double buffering for smooth animation."""
        if not self._front_buffer:
            return
            
        # Convert frame buffer to back buffer with gamma correction
        if isinstance(frame_buffer, bytearray):
            # Bytearray format
            for i in range(0, min(len(frame_buffer), self.num_pixels * 3), 3):
                idx = i // 3
                if idx < self.num_pixels:
                    r = self.gamma_table[frame_buffer[i]]
                    g = self.gamma_table[frame_buffer[i + 1]]
                    b = self.gamma_table[frame_buffer[i + 2]]
                    self._back_buffer[idx] = (r, g, b)
        else:
            # List of tuples format
            for i, (r, g, b) in enumerate(frame_buffer[:self.num_pixels]):
                # Apply gamma correction using lookup table
                r = self.gamma_table[min(255, max(0, r))]
                g = self.gamma_table[min(255, max(0, g))]
                b = self.gamma_table[min(255, max(0, b))]
                self._back_buffer[i] = (r, g, b)
        
        # Swap buffers - update NeoPixel array
        self._front_buffer[:] = self._back_buffer
        self._front_buffer.show()
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a single pixel with serpentine mapping."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
            
        # Use pre-calculated serpentine mapping
        idx = self.serpentine_map.get((x, y), 0)
        
        if 0 <= idx < self.num_pixels:
            # Apply gamma correction
            r = self.gamma_table[min(255, max(0, r))]
            g = self.gamma_table[min(255, max(0, g))]
            b = self.gamma_table[min(255, max(0, b))]
            
            self._back_buffer[idx] = (r, g, b)
            
            if self._front_buffer:
                self._front_buffer[idx] = (r, g, b)
    
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill entire matrix with a single color."""
        # Apply gamma correction
        r = self.gamma_table[min(255, max(0, r))]
        g = self.gamma_table[min(255, max(0, g))]
        b = self.gamma_table[min(255, max(0, b))]
        
        color = (r, g, b)
        self._back_buffer = [color] * self.num_pixels
        
        if self._front_buffer:
            self._front_buffer.fill(color)
    
    def clear(self) -> None:
        """Clear the matrix."""
        self._back_buffer = [(0, 0, 0)] * self.num_pixels
        
        if self._front_buffer:
            self._front_buffer.fill((0, 0, 0))
    
    def show(self) -> None:
        """Update the physical display."""
        if self._front_buffer:
            self._front_buffer.show()
    
    def set_brightness(self, brightness: float) -> None:
        """Set global brightness."""
        self._brightness = max(0.0, min(1.0, brightness))
        
        if self._front_buffer:
            self._front_buffer.brightness = self._brightness
            logger.debug(f"WS2811 brightness set to {self._brightness}")
    
    def cleanup(self) -> None:
        """Clean up resources and turn off display."""
        if self._front_buffer:
            # Turn off all pixels
            self._front_buffer.fill((0, 0, 0))
            self._front_buffer.show()
            
            # Deinitialize
            self._front_buffer.deinit()
            self._front_buffer = None
            
        logger.info("WS2811 driver cleaned up")
    
    def _xy_to_index(self, x: int, y: int) -> int:
        """Convert x,y coordinates to pixel index (legacy method)."""
        # Use pre-calculated mapping for performance
        return self.serpentine_map.get((x, y), 0)