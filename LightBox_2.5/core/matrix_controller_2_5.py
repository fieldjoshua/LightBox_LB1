"""
Optimized Matrix Controller with Double Buffering
================================================

This controller implements the critical optimizations identified in the audit:
- Proper double buffering with SwapOnVSync
- Hardware PWM detection and usage
- Optimized refresh timing
- Performance monitoring
"""

import logging
import time
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logger.warning("rgbmatrix module not available - simulation mode")

class OptimizedMatrixController:
    """High-performance matrix controller with anti-jitter optimizations"""
    
    def __init__(self, config):
        self.config = config
        self.matrix = None
        self.canvas = None
        self.next_canvas = None
        
        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
        
        # Thread safety
        self._render_lock = threading.Lock()
        
        if HARDWARE_AVAILABLE:
            self._initialize_hardware()
        else:
            self._initialize_simulation()
    
    def _initialize_hardware(self):
        """Initialize hardware with optimized settings"""
        options = RGBMatrixOptions()
        
        # Basic configuration
        options.rows = self.config.get('hub75.rows', 64)
        options.cols = self.config.get('hub75.cols', 64)
        options.chain_length = self.config.get('hub75.chain_length', 1)
        options.parallel = self.config.get('hub75.parallel', 1)
        options.hardware_mapping = self.config.get('hub75.hardware_mapping', 'adafruit-hat')
        
        # CRITICAL ANTI-JITTER SETTINGS
        options.gpio_slowdown = self.config.get('hub75.gpio_slowdown', 2)
        options.pwm_bits = self.config.get('hub75.pwm_bits', 8)
        options.pwm_lsb_nanoseconds = self.config.get('hub75.pwm_lsb_nanoseconds', 100)
        options.pwm_dither_bits = self.config.get('hub75.pwm_dither_bits', 2)
        
        # Hardware PWM for stability
        if not self.config.get('hub75.disable_hardware_pulsing', False):
            options.disable_hardware_pulsing = False
            logger.info("Hardware PWM enabled for stable output")
        else:
            options.disable_hardware_pulsing = True
            logger.warning("Using software PWM - consider hardware mod")
        
        # Refresh rate limiting
        if hasattr(options, 'limit_refresh_rate_hz'):
            limit_refresh = self.config.get('hub75.limit_refresh', 150)
            options.limit_refresh_rate_hz = limit_refresh
            logger.info(f"Refresh rate limited to {limit_refresh} Hz")
        
        # Advanced settings
        scan_mode = self.config.get('hub75.scan_mode', 0)
        if scan_mode > 0:
            options.scan_mode = scan_mode
        
        row_addr_type = self.config.get('hub75.row_address_type', 0)
        if row_addr_type > 0:
            options.row_address_type = row_addr_type
        
        multiplexing = self.config.get('hub75.multiplexing', 0)
        if multiplexing > 0:
            options.multiplexing = multiplexing
        
        # Brightness
        brightness = int(self.config.get('brightness', 0.8) * 100)
        options.brightness = brightness
        
        try:
            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()
            self.next_canvas = self.matrix.CreateFrameCanvas()
            
            logger.info(f"Matrix initialized: {options.cols}x{options.rows}")
            logger.info(f"Optimizations: PWM={options.pwm_bits}bit, "
                       f"GPIO_slowdown={options.gpio_slowdown}, "
                       f"HW_PWM={'enabled' if not options.disable_hardware_pulsing else 'disabled'}")
            
        except Exception as e:
            logger.error(f"Failed to initialize matrix: {e}")
            self._initialize_simulation()
    
    def _initialize_simulation(self):
        """Initialize simulation mode"""
        self.matrix = None
        self.canvas = None
        logger.info("Matrix controller in simulation mode")
    
    @contextmanager
    def render_frame(self):
        """Context manager for double-buffered rendering"""
        with self._render_lock:
            if self.canvas:
                self.canvas.Clear()
                yield self.canvas
                # CRITICAL: Use SwapOnVSync for tear-free animation
                self.canvas = self.matrix.SwapOnVSync(self.canvas)
                self._update_fps()
            else:
                yield None
    
    def set_pixel(self, x, y, r, g, b):
        """Set individual pixel with bounds checking"""
        if self.canvas and 0 <= x < self.matrix.width and 0 <= y < self.matrix.height:
            self.canvas.SetPixel(x, y, r, g, b)
    
    def clear(self):
        """Clear the display"""
        if self.canvas:
            self.canvas.Clear()
            if self.matrix:
                self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def _update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
            
            if self.config.get('hub75.show_refresh_rate', False):
                logger.info(f"FPS: {self.fps:.1f}")
    
    def get_fps(self):
        """Get current FPS"""
        return self.fps
    
    def get_dimensions(self):
        """Get matrix dimensions"""
        if self.matrix:
            return self.matrix.width, self.matrix.height
        else:
            return self.config.get('hub75.cols', 64), self.config.get('hub75.rows', 64)
    
    def shutdown(self):
        """Clean shutdown"""
        if self.matrix:
            self.clear()
        logger.info("Matrix controller shutdown")
