"""
GPIO Button handler for physical controls
Supports multiple buttons with debouncing and callbacks
"""

import RPi.GPIO as GPIO
import time
import threading


class ButtonController:
    """Handle physical button inputs with debouncing"""
    
    def __init__(self, led_controller=None):
        self.led_controller = led_controller
        self.buttons = {}
        self.callbacks = {}
        
        # Configure GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Default button configuration
        self.button_pins = {
            'mode': 23,      # Switch animation mode
            'brightness_up': 24,
            'brightness_down': 25,
            'speed_up': 8,
            'speed_down': 7,
            'preset': 12     # Cycle through presets
        }
        
        self.setup_buttons()
        
    def setup_buttons(self):
        """Initialize button pins and callbacks"""
        for name, pin in self.button_pins.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.buttons[name] = {
                'pin': pin,
                'last_state': GPIO.HIGH,
                'last_time': 0
            }
            
        # Register default callbacks
        self.register_callback('mode', self.on_mode_button)
        self.register_callback('brightness_up', self.on_brightness_up)
        self.register_callback('brightness_down', self.on_brightness_down)
        self.register_callback('speed_up', self.on_speed_up)
        self.register_callback('speed_down', self.on_speed_down)
        self.register_callback('preset', self.on_preset_button)
        
    def register_callback(self, button_name, callback):
        """Register a callback function for a button"""
        if button_name in self.buttons:
            self.callbacks[button_name] = callback
            
    def start(self):
        """Start button monitoring thread"""
        self.running = True
        self.thread = threading.Thread(target=self.monitor_buttons, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop button monitoring"""
        self.running = False
        GPIO.cleanup()
        
    def cleanup(self):
        """Clean up GPIO resources - alias for stop()"""
        self.stop()
        
    def monitor_buttons(self):
        """Main button monitoring loop with debouncing"""
        while self.running:
            for name, button in self.buttons.items():
                current_state = GPIO.input(button['pin'])
                current_time = time.time()
                
                # Check for state change with debouncing
                if (current_state != button['last_state'] and 
                        current_time - button['last_time'] > 0.1):  # 100ms debounce
                    
                    if current_state == GPIO.LOW:  # Button pressed
                        if name in self.callbacks:
                            try:
                                self.callbacks[name]()
                            except Exception as e:
                                print(f"Error in button callback {name}: {e}")
                    
                    button['last_state'] = current_state
                    button['last_time'] = current_time
                    
            time.sleep(0.01)  # 10ms polling interval
            
    # Default button callbacks
    def on_mode_button(self):
        """Cycle through animation programs"""
        if self.led_controller:
            programs = list(self.led_controller.programs.keys())
            current_idx = programs.index(self.led_controller.current_program)
            next_idx = (current_idx + 1) % len(programs)
            self.led_controller.switch_program(programs[next_idx])
            print(f"Switched to program: {programs[next_idx]}")
            
    def on_brightness_up(self):
        """Increase brightness"""
        if self.led_controller:
            new_brightness = min(1.0, 
                               self.led_controller.config.BRIGHTNESS + 0.1)
            self.led_controller.update_config({'BRIGHTNESS': new_brightness})
            print(f"Brightness: {int(new_brightness * 100)}%")
            
    def on_brightness_down(self):
        """Decrease brightness"""
        if self.led_controller:
            new_brightness = max(0.0, 
                               self.led_controller.config.BRIGHTNESS - 0.1)
            self.led_controller.update_config({'BRIGHTNESS': new_brightness})
            print(f"Brightness: {int(new_brightness * 100)}%")
            
    def on_speed_up(self):
        """Increase animation speed"""
        if self.led_controller:
            new_speed = min(5.0, self.led_controller.config.SPEED + 0.2)
            self.led_controller.update_config({'SPEED': new_speed})
            print(f"Speed: {new_speed}x")
            
    def on_speed_down(self):
        """Decrease animation speed"""
        if self.led_controller:
            new_speed = max(0.1, self.led_controller.config.SPEED - 0.2)
            self.led_controller.update_config({'SPEED': new_speed})
            print(f"Speed: {new_speed}x")
            
    def on_preset_button(self):
        """Cycle through presets"""
        # This would load presets from the presets directory
        print("Preset button pressed")
        
    def add_button(self, name, pin, callback=None):
        """Add a custom button"""
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.buttons[name] = {
            'pin': pin,
            'last_state': GPIO.HIGH,
            'last_time': 0
        }
        if callback:
            self.register_callback(name, callback)