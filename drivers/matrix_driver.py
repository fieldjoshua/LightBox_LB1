"""
Abstract base class for all matrix drivers.
Defines the interface that both WS2811 and HUB75 drivers must implement.
"""

# flake8: noqa: E501  # allow occasional long log strings

from abc import ABC, abstractmethod
from typing import Tuple, List, Union
import logging
import platform

logger = logging.getLogger(__name__)


class MatrixDriver(ABC):
    """Abstract base class for all matrix drivers."""
    
    def __init__(self, config):
        self.config = config
        self.width = 0
        self.height = 0
        self.num_pixels = 0
        self._brightness = 1.0
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the matrix hardware.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update(self, frame_buffer: Union[List[Tuple[int, int, int]], bytearray]) -> None:
        """Update the physical matrix with frame data.
        
        Args:
            frame_buffer: Either a list of (R, G, B) tuples or a bytearray
        """
        pass
    
    @abstractmethod
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a single pixel color.
        
        Args:
            x: X coordinate
            y: Y coordinate
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        pass
    
    @abstractmethod
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill entire matrix with a single color.
        
        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the matrix (turn all pixels off)."""
        pass
    
    @abstractmethod
    def show(self) -> None:
        """Update the physical display with current pixel data."""
        pass
    
    @abstractmethod
    def set_brightness(self, brightness: float) -> None:
        """Set global brightness.
        
        Args:
            brightness: Brightness value (0.0-1.0)
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources and turn off display."""
        pass
    
    @property
    def brightness(self) -> float:
        """Get current brightness setting."""
        return self._brightness
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class SimulatedMatrixDriver(MatrixDriver):
    """Simulated matrix driver for testing without hardware."""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Determine dimensions based on matrix type
        if config.get("matrix_type") == "hub75":
            self.width = config.get("hub75", {}).get("cols", 64)
            self.height = config.get("hub75", {}).get("rows", 64)
        else:
            self.width = config.get("ws2811", {}).get("width", 10)
            self.height = config.get("ws2811", {}).get("height", 10)
            
        self.num_pixels = self.width * self.height
        self.pixels = [(0, 0, 0)] * self.num_pixels
        
        logger.info(f"Initialized simulated matrix: {self.width}x{self.height}")
    
    def initialize(self) -> bool:
        """Initialize simulated matrix."""
        logger.info("Simulated matrix initialized")
        return True
    
    def update(self, frame_buffer: Union[List[Tuple[int, int, int]], bytearray]) -> None:
        """Update simulated matrix."""
        if isinstance(frame_buffer, bytearray):
            # Convert bytearray to tuples
            for i in range(0, len(frame_buffer), 3):
                idx = i // 3
                if idx < self.num_pixels:
                    self.pixels[idx] = (
                        frame_buffer[i],
                        frame_buffer[i + 1],
                        frame_buffer[i + 2]
                    )
        else:
            # Direct list copy
            self.pixels = list(frame_buffer[:self.num_pixels])
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set pixel in simulated matrix."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            
            # Apply brightness
            r = int(r * self._brightness)
            g = int(g * self._brightness)
            b = int(b * self._brightness)
            
            self.pixels[idx] = (r, g, b)
    
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill simulated matrix."""
        # Apply brightness
        r = int(r * self._brightness)
        g = int(g * self._brightness)
        b = int(b * self._brightness)
        
        self.pixels = [(r, g, b)] * self.num_pixels
    
    def clear(self) -> None:
        """Clear simulated matrix."""
        self.pixels = [(0, 0, 0)] * self.num_pixels
    
    def show(self) -> None:
        """Update simulated display (no-op)."""
        pass
    
    def set_brightness(self, brightness: float) -> None:
        """Set brightness for simulation."""
        self._brightness = max(0.0, min(1.0, brightness))
        logger.debug(f"Simulated brightness set to {self._brightness}")
    
    def cleanup(self) -> None:
        """Clean up simulated matrix."""
        self.clear()
        logger.info("Simulated matrix cleaned up")
    
    def get_frame(self) -> List[Tuple[int, int, int]]:
        """Get current frame for testing/visualization."""
        return self.pixels.copy()


def create_matrix_driver(config) -> MatrixDriver:
    """Factory function to create appropriate matrix driver.
    
    Args:
        config: Configuration manager instance
        
    Returns:
        MatrixDriver: Appropriate driver instance based on configuration
    """
    matrix_type = config.get("matrix_type", "ws2811")
    
    # Check if we should use simulation mode
    try:
        import RPi.GPIO as _gpio  # noqa: F401
        hardware_available = True
    except ImportError:
        hardware_available = False
        logger.warning("RPi.GPIO not available, using mock driver")
    
    # Check if we're on a Raspberry Pi
    is_raspberry_pi = platform.machine().startswith('arm') or platform.machine().startswith('aarch')
    
    # Use mock driver if not on Pi or simulation mode is enabled
    if not hardware_available or not is_raspberry_pi or config.get("simulation_mode", False):
        try:
            from .mock_driver import MockDriver
            logger.info("Using MockDriver for development/testing")
            return MockDriver(config)
        except ImportError:
            logger.warning("MockDriver not available, falling back to SimulatedMatrixDriver")
            return SimulatedMatrixDriver(config)
    
    if matrix_type == "hub75":
        # Prefer the newer controller-based driver; fall back to the legacy
        # implementation if the new adapter cannot be imported (e.g. missing
        # dependencies on non-Pi hosts).
        try:
            from .hub75_controller_driver import HUB75ControllerDriver  # noqa: E501

            return HUB75ControllerDriver(config)
        except ImportError as e:
            logger.warning(
                "New HUB75ControllerDriver unavailable (%s). "
                "Falling back to legacy HUB75Driver.",
                e,
            )  # noqa: E501
            try:
                from .hub75_driver import HUB75Driver
                return HUB75Driver(config)
            except ImportError as e2:
                logger.error(
                    "Failed to import legacy HUB75 driver: %s", e2
                )
                logger.warning("Falling back to mock driver")
                try:
                    from .mock_driver import MockDriver
                    return MockDriver(config)
                except ImportError:
                    return SimulatedMatrixDriver(config)
    else:
        try:
            from .ws2811_driver import WS2811Driver
            return WS2811Driver(config)
        except ImportError as e:
            logger.error(f"Failed to import WS2811 driver: {e}")
            logger.warning("Falling back to mock driver")
            try:
                from .mock_driver import MockDriver
                return MockDriver(config)
            except ImportError:
                return SimulatedMatrixDriver(config)