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
from typing import Tuple, List, Union, Optional
from .matrix_driver import MatrixDriver

logger = logging.getLogger(__name__)

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    RGB_MATRIX_AVAILABLE = True
except ImportError:
    RGB_MATRIX_AVAILABLE = False
    logger.warning("rgbmatrix library not available - install with install_rgb_matrix.sh")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False


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
            options.hardware_mapping = 'adafruit-hat'  # Adafruit HAT/Bonnet
            
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
            
            # Set brightness (0-100%)
            options.brightness = int(self.config.get("brightness", 0.8) * 100)
            
            # Show refresh rate for debugging
            options.show_refresh_rate = self.config.get("performance", {}).get("show_refresh_rate", False)
            
            # Enable hardware PWM if GPIO4-GPIO18 jumper is soldered
            # -----------------------------------------------------
            # Hardware PWM eliminates flicker by using hardware pulse generation
            # This requires physically soldering a jumper between GPIO4 and GPIO18
            # Without this jumper, software PWM is used which can cause flickering lines
            if self._detect_hardware_pwm():
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
            limit_refresh = self.hub_config.get("limit_refresh", 0)
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
            if self._check_cpu_isolation():
                logger.info("CPU isolation detected - core 3 dedicated to matrix")
            else:
                logger.warning("CPU isolation not enabled - add 'isolcpus=3' to /boot/cmdline.txt")
            
            # Create matrix
            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()
            
            # Try to load graphics module for text support
            try:
                from rgbmatrix import graphics
                self.graphics = graphics
                self.font = graphics.Font()
                # Try to load a default font
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "../../../fonts/7x13.bdf"  # From rgbmatrix samples
                ]
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            self.font.LoadFont(font_path)
                            logger.info(f"Loaded font: {font_path}")
                            break
                        except:
                            pass
            except:
                logger.warning("Graphics module not available for text rendering")
            
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
        
        The hardware PWM jumper connects GPIO4 to GPIO18, enabling hardware
        pulse generation instead of software PWM. This eliminates flicker
        and horizontal line artifacts common with software PWM.
        """
        if not GPIO_AVAILABLE:
            return False
            
        try:
            # Save current GPIO state
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configure pins
            GPIO.setup(4, GPIO.OUT)
            GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            # Test connection
            GPIO.output(4, GPIO.HIGH)
            time.sleep(0.001)
            connected = GPIO.input(18) == GPIO.HIGH
            GPIO.output(4, GPIO.LOW)
            
            # Cleanup
            GPIO.cleanup([4, 18])
            
            return connected
            
        except Exception as e:
            logger.debug(f"Hardware PWM detection failed: {e}")
            return False
    
    def _check_cpu_isolation(self) -> bool:
        """Check if CPU isolation is enabled (isolcpus=3).
        
        CPU isolation reserves a dedicated core for the LED matrix update thread,
        preventing system processes from interrupting the display refresh.
        This significantly improves performance and reduces flicker on
        multi-core Raspberry Pi models (3B+, 4).
        """
        try:
            with open('/proc/cmdline', 'r') as f:
                cmdline = f.read()
                return 'isolcpus=3' in cmdline
        except:
            return False
    
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
        
        # Hardware accelerated buffer swap - key to smooth animation!
        # This is the SwapOnVSync() that ensures tear-free updates
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a single pixel."""
        if self.canvas and 0 <= x < self.width and 0 <= y < self.height:
            self.canvas.SetPixel(x, y, r, g, b)
    
    def fill(self, r: int, g: int, b: int) -> None:
        """Fill entire matrix with a single color."""
        if not self.canvas:
            return
            
        for y in range(self.height):
            for x in range(self.width):
                self.canvas.SetPixel(x, y, r, g, b)
    
    def clear(self) -> None:
        """Clear the matrix."""
        if self.canvas:
            self.canvas.Clear()
    
    def show(self) -> None:
        """Update the physical display (swap buffers)."""
        if self.matrix and self.canvas:
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def set_brightness(self, brightness: float) -> None:
        """Set global brightness."""
        self._brightness = max(0.0, min(1.0, brightness))
        
        if self.matrix:
            # Convert to percentage (0-100)
            brightness_percent = int(self._brightness * 100)
            self.matrix.brightness = brightness_percent
            logger.debug(f"HUB75 brightness set to {brightness_percent}%")
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int] = (255, 255, 255)) -> int:
        """Draw text using graphics module if available.
        
        Returns:
            int: Width of rendered text in pixels
        """
        if self.graphics and self.font and self.canvas:
            text_color = self.graphics.Color(*color)
            return self.graphics.DrawText(self.canvas, self.font, x, y, text_color, text)
        return 0
    
    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: Tuple[int, int, int]):
        """Draw a line using graphics module if available."""
        if self.graphics and self.canvas:
            line_color = self.graphics.Color(*color)
            self.graphics.DrawLine(self.canvas, x0, y0, x1, y1, line_color)
    
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """Draw a circle using graphics module if available."""
        if self.graphics and self.canvas:
            circle_color = self.graphics.Color(*color)
            self.graphics.DrawCircle(self.canvas, x, y, radius, circle_color)
    
    def cleanup(self) -> None:
        """Clean up resources and turn off display."""
        if self.matrix:
            # Clear display
            if self.canvas:
                self.canvas.Clear()
                self.matrix.SwapOnVSync(self.canvas)
            
            # Note: rgbmatrix doesn't have explicit cleanup
            # The matrix will turn off when the process exits
            
        logger.info("HUB75 driver cleaned up")