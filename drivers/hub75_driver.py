"""
Hardware-accelerated HUB75 driver with all Henner Zeller optimizations.
Implements double buffering, hardware PWM detection, and CPU isolation support.

This driver implements best practices from Henner Zeller's rpi-rgb-led-matrix library:
- Double buffering with SwapOnVSync() for tear-free animation
- Hardware PWM detection (GPIO4-GPIO18 jumper) for flicker elimination
- CPU isolation detection (isolcpus=3) for dedicated update thread
- Optimal GPIO slowdown settings for different Pi models
- PWM bit depth and refresh rate balancing
"""

import logging
import time
import os
import sys
from typing import Tuple, List, Union, Optional
from pathlib import Path
from .matrix_driver import MatrixDriver

logger = logging.getLogger(__name__)

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    RGB_MATRIX_AVAILABLE = True
except ImportError:
    RGB_MATRIX_AVAILABLE = False
    logger.warning("rgbmatrix library not available - install with install_rgb_matrix.sh")

# Import hardware detection utilities
try:
    # Add parent directory to path for local imports
    sys.path.append(str(Path(__file__).parent.parent))
    from scripts.util.hardware_detect import detect_hardware_pwm, check_cpu_isolation, get_system_info
    HARDWARE_DETECT_AVAILABLE = True
except ImportError:
    HARDWARE_DETECT_AVAILABLE = False
    logger.warning("Hardware detection utilities not available")


class HUB75Driver(MatrixDriver):
    """Hardware-accelerated HUB75 driver with all Zeller optimizations."""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Get HUB75 configuration
        hub_config = config.get("hub75", {})
        self.width = hub_config.get("cols", 64)
        self.height = hub_config.get("rows", 64)
        self.num_pixels = self.width * self.height
        
        # Store config for initialization
        self.hub_config = hub_config
        self.matrix = None
        self.canvas = None
        self.refresh_rate = 0
        
        # Graphics module for text/shapes (optional)
        self.graphics = None
        self.font = None
        
        logger.info(f"HUB75 driver configured: {self.width}x{self.height}")
    
    def initialize(self) -> bool:
        """Initialize the HUB75 matrix with all optimizations."""
        if not RGB_MATRIX_AVAILABLE:
            logger.error("rgbmatrix library not available")
            return False
            
        try:
            # Configure with optimization guide settings from Henner Zeller's library
            options = RGBMatrixOptions()
            
            # Basic configuration
            options.rows = self.hub_config.get("rows", 64)
            options.cols = self.hub_config.get("cols", 64)
            options.chain_length = self.hub_config.get("chain_length", 1)
            options.parallel = self.hub_config.get("parallel", 1)
            options.hardware_mapping = self.hub_config.get("hardware_mapping", 'adafruit-hat')
            
            # Critical performance settings from optimization guide
            # -----------------------------------------------------
            # gpio_slowdown: Adjusts timing for different Pi models
            # - Pi 1: Use value 1
            # - Pi 2/Zero: Use value 2
            # - Pi 3/4: Use value 4 (prevents flickering)
            options.gpio_slowdown = self.hub_config.get("gpio_slowdown", 4)  # Pi 3B+ optimal
            
            # pwm_bits: Balance between color depth and refresh rate
            # - Higher values (11): Better color depth but slower refresh
            # - Lower values (7): Less color depth but faster refresh
            options.pwm_bits = self.hub_config.get("pwm_bits", 11)  # Balance color/speed
            
            # pwm_lsb_nanoseconds: Fine-tune PWM timing
            # - Lower values: Faster refresh but may cause instability
            # - Higher values: More stable but slower refresh
            options.pwm_lsb_nanoseconds = self.hub_config.get("pwm_lsb_nanoseconds", 130)
            
            # pwm_dither_bits: Improves color smoothness through dithering
            # - Higher values (1-2): Better color accuracy but may introduce noise
            # - 0: No dithering (default)
            options.pwm_dither_bits = self.hub_config.get("pwm_dither_bits", 0)
            
            # Set brightness (0-100%)
            options.brightness = int(self.config.get("brightness", 0.8) * 100)
            
            # Show refresh rate for debugging
            options.show_refresh_rate = self.hub_config.get("show_refresh_rate", False)
            
            # Enable hardware PWM if GPIO4-GPIO18 jumper is soldered
            # -----------------------------------------------------
            # Hardware PWM eliminates flicker by using hardware pulse generation
            # This requires physically soldering a jumper between GPIO4 and GPIO18
            # Without this jumper, software PWM is used which can cause flickering lines
            hardware_pwm_setting = self.hub_config.get("hardware_pwm", "auto")
            hardware_pwm_mod = self.config.get("hardware", {}).get("hardware_pwm_mod", False)
            
            # Detect hardware PWM using our utility
            hardware_pwm_detected = self._detect_hardware_pwm()
            
            if hardware_pwm_setting == "on" or (hardware_pwm_setting == "auto" and (hardware_pwm_mod or hardware_pwm_detected)):
                options.disable_hardware_pulsing = False
                logger.info("Hardware PWM enabled - eliminates flicker!")
            else:
                options.disable_hardware_pulsing = True
                logger.warning("Hardware PWM not detected - consider soldering GPIO4-GPIO18 jumper")
            
            # Frame rate limiting for stability
            # -----------------------------------------------------
            # Setting a fixed refresh rate can stabilize animations under load
            # 0 = no limit (maximum possible refresh rate)
            # 120 = limit to 120 Hz (good balance for Pi 3B+)
            limit_refresh = self.hub_config.get("limit_refresh", 120)
            if limit_refresh > 0:
                options.limit_refresh_rate_hz = limit_refresh
                logger.info(f"Refresh rate limited to {limit_refresh} Hz")
            
            # Additional optimizations
            # -----------------------------------------------------
            # scan_mode: 0=progressive, 1=interlaced
            # row_address_type: 0-4 for different panel types
            # multiplexing: 0-17 for different multiplexing schemes
            options.scan_mode = self.hub_config.get("scan_mode", 0)  # Progressive scan
            options.row_address_type = self.hub_config.get("row_address_type", 0)
            options.multiplexing = self.hub_config.get("multiplexing", 0)
            
            # CPU isolation check (requires isolcpus=3 in boot cmdline)
            # -----------------------------------------------------
            # On multi-core Pis (3B+/4), dedicating a CPU core to the matrix
            # significantly improves performance and stability
            # Add 'isolcpus=3' to /boot/cmdline.txt to enable
            cpu_isolation_enabled = self.config.get("performance", {}).get("cpu_isolation", True)
            cpu_isolation_detected = self._check_cpu_isolation()
            
            if cpu_isolation_enabled:
                if cpu_isolation_detected:
                    logger.info("CPU isolation detected - core 3 dedicated to matrix")
                else:
                    logger.warning("CPU isolation requested but not detected - add 'isolcpus=3' to /boot/cmdline.txt")
            
            # Create matrix
            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()
            
            # Get refresh rate if available
            if hasattr(self.matrix, 'refresh_rate'):
                self.refresh_rate = self.matrix.refresh_rate
            elif hasattr(self.matrix, 'led_refresh_rate'):
                self.refresh_rate = self.matrix.led_refresh_rate
            
            # Try to load graphics module for text support
            try:
                from rgbmatrix import graphics
                self.graphics = graphics
                self.font = graphics.Font()
                # Try to load a default font
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                    "../../../fonts/7x13.bdf",  # From rgbmatrix samples
                    "fonts/7x13.bdf"
                ]
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            self.font.LoadFont(font_path)
                            logger.info(f"Loaded font: {font_path}")
                            break
                        except Exception as e:
                            logger.debug(f"Failed to load font {font_path}: {e}")
            except Exception as e:
                logger.warning(f"Graphics module not available for text rendering: {e}")
            
            # Clear display
            self.canvas.Clear()
            self.matrix.SwapOnVSync(self.canvas)
            
            logger.info("HUB75 hardware initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize HUB75: {e}")
            return False
    
    def _detect_hardware_pwm(self) -> bool:
        """Check if GPIO4-GPIO18 jumper is connected for hardware PWM.
        
        Uses the hardware_detect utility if available, otherwise falls back
        to basic detection.
        """
        if HARDWARE_DETECT_AVAILABLE:
            return detect_hardware_pwm()
            
        # Fallback to a basic check
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            GPIO.setup(4, GPIO.OUT)
            GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            GPIO.output(4, GPIO.HIGH)
            time.sleep(0.001)
            connected = GPIO.input(18) == GPIO.HIGH
            GPIO.output(4, GPIO.LOW)
            
            GPIO.cleanup([4, 18])
            return connected
            
        except Exception as e:
            logger.debug(f"Hardware PWM detection failed: {e}")
            # If we can't detect, assume it's not connected
            return False
    
    def _check_cpu_isolation(self) -> bool:
        """Check if CPU isolation is enabled (isolcpus=3).
        
        Uses the hardware_detect utility if available, otherwise falls back
        to basic detection.
        """
        if HARDWARE_DETECT_AVAILABLE:
            return check_cpu_isolation()
            
        # Fallback to basic check
        try:
            with open('/proc/cmdline', 'r') as f:
                cmdline = f.read()
                return 'isolcpus=3' in cmdline
        except Exception as e:
            logger.debug(f"CPU isolation check failed: {e}")
            return False
    
    def get_hardware_status(self) -> dict:
        """Get hardware status information.
        
        Returns:
            dict: Hardware status information
        """
        status = {
            "hardware_pwm": self._detect_hardware_pwm(),
            "cpu_isolation": self._check_cpu_isolation(),
            "refresh_rate": self.refresh_rate
        }
        
        # Add more detailed info if hardware_detect is available
        if HARDWARE_DETECT_AVAILABLE:
            try:
                system_info = get_system_info()
                status.update(system_info)
            except Exception as e:
                logger.debug(f"Failed to get system info: {e}")
                
        return status
    
    def update(self, frame_buffer: Union[List[Tuple[int, int, int]], bytearray]) -> None:
        """Update using hardware double buffering with SwapOnVSync.
        
        Double buffering is critical for smooth, tear-free animation:
        1. Draw to an off-screen canvas
        2. Swap the canvas with SwapOnVSync() when complete
        3. This ensures the entire frame updates at once
        
        Args:
            frame_buffer: Either a list of (r,g,b) tuples or a bytearray
        """
        if not self.matrix or not self.canvas:
            return
            
        # Render to off-screen canvas for flicker-free updates
        if isinstance(frame_buffer, bytearray):
            # Bytearray format - fast path
            idx = 0
            for y in range(self.height):
                for x in range(self.width):
                    if idx + 2 < len(frame_buffer):
                        r = frame_buffer[idx]
                        g = frame_buffer[idx + 1]
                        b = frame_buffer[idx + 2]
                        self.canvas.SetPixel(x, y, r, g, b)
                        idx += 3
        else:
            # List of tuples format
            idx = 0
            for y in range(self.height):
                for x in range(self.width):
                    if idx < len(frame_buffer):
                        r, g, b = frame_buffer[idx]
                        self.canvas.SetPixel(x, y, r, g, b)
                        idx += 1
        
        # Swap the buffer - this is the critical operation for tear-free animation
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a single pixel on the off-screen canvas."""
        if self.canvas and 0 <= x < self.width and 0 <= y < self.height:
            self.canvas.SetPixel(x, y, r, g, b)
    
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill the entire display with a single color."""
        if self.canvas:
            for y in range(self.height):
                for x in range(self.width):
                    self.canvas.SetPixel(x, y, r, g, b)
            
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def clear(self) -> None:
        """Clear the display (set all pixels to black)."""
        if self.canvas:
            self.canvas.Clear()
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def show(self) -> None:
        """Update the display with the current canvas."""
        if self.matrix and self.canvas:
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def set_brightness(self, brightness: float) -> None:
        """Set display brightness (0.0-1.0)."""
        if self.matrix:
            # rgbmatrix brightness is 0-100
            brightness_int = max(0, min(100, int(brightness * 100)))
            self.matrix.brightness = brightness_int
            logger.debug(f"Brightness set to {brightness_int}%")
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int] = (255, 255, 255)) -> int:
        """Draw text on the canvas using loaded font."""
        if not self.graphics or not self.font or not self.canvas:
            return 0
            
        # Create RGB color
        rgb_color = self.graphics.Color(color[0], color[1], color[2])
        
        # Draw text to canvas and return length
        return self.graphics.DrawText(self.canvas, self.font, x, y, rgb_color, text)
    
    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]):
        """Draw a line between two points."""
        if not self.graphics or not self.canvas:
            return
            
        rgb_color = self.graphics.Color(color[0], color[1], color[2])
        self.graphics.DrawLine(self.canvas, x0, y0, x1, y1, rgb_color)
    
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """Draw a circle with center (x,y) and radius."""
        if not self.graphics or not self.canvas:
            return
            
        rgb_color = self.graphics.Color(color[0], color[1], color[2])
        self.graphics.DrawCircle(self.canvas, x, y, radius, rgb_color)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Nothing specific needed for RGB matrix cleanup
        pass