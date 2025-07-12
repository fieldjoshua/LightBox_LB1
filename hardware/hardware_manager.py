"""
Unified hardware interface management.
Handles GPIO buttons and OLED display with graceful degradation.
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import hardware dependencies
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - buttons disabled")


class HardwareManager:
    """Unified hardware interface management."""
    
    def __init__(self, config, conductor):
        self.config = config
        self.conductor = conductor
        self.buttons = None
        self.oled = None
        
        # Initialize hardware with graceful degradation
        self._init_buttons()
        self._init_oled()
    
    def _init_buttons(self):
        """Initialize GPIO buttons with error handling."""
        if not GPIO_AVAILABLE:
            return
            
        try:
            from .buttons import ButtonController
            # ButtonController expects led_controller as parameter
            self.buttons = ButtonController(self.conductor)
            logger.info("GPIO buttons initialized")
        except Exception as e:
            logger.warning(f"Buttons unavailable: {e}")
    
    def _init_oled(self):
        """Initialize OLED display with error handling."""
        try:
            from .oled import OLEDDisplay
            self.oled = OLEDDisplay(self.config, self.conductor)
            logger.info("OLED display initialized")
        except Exception as e:
            logger.warning(f"OLED unavailable: {e}")
    
    def process_events(self):
        """Process hardware events (called from main loop)."""
        # Button processing is handled by interrupts
        # This is for any polling-based hardware
        pass
    
    def cleanup(self):
        """Clean up hardware resources."""
        if self.buttons:
            self.buttons.cleanup()
        
        if self.oled:
            self.oled.cleanup()


class ButtonController:
    """GPIO button controller with debouncing."""
    
    # Button GPIO pins
    PINS = {
        'mode': 23,
        'brightness_up': 24,
        'brightness_down': 25,
        'speed_up': 8,
        'speed_down': 7,
        'preset': 12
    }
    
    def __init__(self, config, conductor):
        self.config = config
        self.conductor = conductor
        self._last_press_time = {}
        self._debounce_time = 0.2  # 200ms debounce
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Setup GPIO pins for buttons."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all button pins
        for button, pin in self.PINS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin,
                GPIO.FALLING,
                callback=lambda ch, b=button: self._button_callback(b),
                bouncetime=200
            )
        
        logger.info("GPIO buttons configured")
    
    def _button_callback(self, button: str):
        """Handle button press with debouncing."""
        current_time = time.time()
        
        # Check debounce
        if button in self._last_press_time:
            if current_time - self._last_press_time[button] < self._debounce_time:
                return
        
        self._last_press_time[button] = current_time
        
        # Handle button action
        try:
            if button == 'mode':
                self._cycle_animation()
            elif button == 'brightness_up':
                self._adjust_brightness(0.1)
            elif button == 'brightness_down':
                self._adjust_brightness(-0.1)
            elif button == 'speed_up':
                self._adjust_speed(0.2)
            elif button == 'speed_down':
                self._adjust_speed(-0.2)
            elif button == 'preset':
                self._cycle_preset()
                
            logger.info(f"Button pressed: {button}")
            
        except Exception as e:
            logger.error(f"Error handling button {button}: {e}")
    
    def _cycle_animation(self):
        """Cycle to next animation."""
        animations = list(self.conductor.animations.keys())
        if not animations:
            return
        
        current = self.conductor.current_animation.name if self.conductor.current_animation else None
        try:
            current_idx = animations.index(current)
            next_idx = (current_idx + 1) % len(animations)
        except ValueError:
            next_idx = 0
        
        self.conductor.set_animation(animations[next_idx])
    
    def _adjust_brightness(self, delta: float):
        """Adjust brightness up or down."""
        current = self.config.get("brightness", 0.8)
        new_brightness = max(0.1, min(1.0, current + delta))
        self.conductor.set_brightness(new_brightness)
    
    def _adjust_speed(self, delta: float):
        """Adjust animation speed."""
        current = self.config.get("speed", 1.0)
        new_speed = max(0.1, min(5.0, current + delta))
        self.conductor.set_speed(new_speed)
    
    def _cycle_preset(self):
        """Cycle through saved presets."""
        # TODO: Implement preset cycling
        logger.info("Preset cycling not yet implemented")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup()
        logger.info("GPIO buttons cleaned up")


class OLEDDisplay:
    """OLED status display controller."""
    
    def __init__(self, config, conductor):
        self.config = config
        self.conductor = conductor
        self.display = None
        self._update_thread = None
        self._running = False
        
        self._init_display()
    
    def _init_display(self):
        """Initialize OLED display."""
        try:
            import board
            import busio
            from PIL import Image, ImageDraw, ImageFont
            import adafruit_ssd1306
            
            # Create I2C interface
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Create display (128x32 or 128x64)
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            # Start update thread
            self._running = True
            self._update_thread = threading.Thread(
                target=self._update_loop,
                daemon=True
            )
            self._update_thread.start()
            
            logger.info("OLED display initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize OLED: {e}")
            self.display = None
    
    def _update_loop(self):
        """Update display periodically."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image buffer
        image = Image.new("1", (128, 32))
        draw = ImageDraw.Draw(image)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        while self._running and self.display:
            try:
                # Clear image
                draw.rectangle((0, 0, 128, 32), outline=0, fill=0)
                
                # Get status
                status = self.conductor.get_status()
                
                # Draw status info
                draw.text((0, 0), f"Anim: {status.get('animation', 'None')}", font=font, fill=255)
                draw.text((0, 12), f"FPS: {status['performance']['fps']['current']:.1f}", font=font, fill=255)
                draw.text((0, 24), f"Brightness: {int(status['brightness'] * 100)}%", font=font, fill=255)
                
                # Update display
                self.display.image(image)
                self.display.show()
                
                # Update every second
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"OLED update error: {e}")
                time.sleep(5.0)
    
    def cleanup(self):
        """Clean up display resources."""
        self._running = False
        
        if self._update_thread:
            self._update_thread.join(timeout=2.0)
        
        if self.display:
            self.display.fill(0)
            self.display.show()
        
        logger.info("OLED display cleaned up")