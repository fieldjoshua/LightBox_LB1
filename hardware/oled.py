"""
OLED Display controller for showing system status
Supports SSD1306 128x64 I2C displays
"""

import time
import threading
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import busio

class OLEDDisplay:
    """Control an OLED display for status information"""
    
    def __init__(self, led_controller=None):
        self.led_controller = led_controller
        self.running = False
        self.display = None
        
        try:
            # Initialize I2C
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize display (128x64 SSD1306)
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            # Create image buffer
            self.width = self.display.width
            self.height = self.display.height
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            
            # Load font (you may need to adjust path)
            try:
                self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10)
                self.small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
            except:
                # Fallback to default font
                self.font = ImageFont.load_default()
                self.small_font = self.font
                
            print("OLED display initialized")
            
        except Exception as e:
            print(f"Error initializing OLED display: {e}")
            self.display = None
            
    def start(self):
        """Start display update thread"""
        if self.display:
            self.running = True
            self.thread = threading.Thread(target=self.update_loop, daemon=True)
            self.thread.start()
            
    def stop(self):
        """Stop display updates"""
        self.running = False
        if self.display:
            self.clear()
            
    def clear(self):
        """Clear the display"""
        if self.display:
            self.display.fill(0)
            self.display.show()
            
    def update_loop(self):
        """Main display update loop"""
        while self.running:
            try:
                self.update_display()
                time.sleep(0.5)  # Update every 500ms
            except Exception as e:
                print(f"Error updating OLED: {e}")
                time.sleep(1)
                
    def update_display(self):
        """Update display with current status"""
        if not self.display or not self.led_controller:
            return
            
        # Clear image
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        
        # Title
        self.draw.text((2, 0), "LightBox Status", font=self.font, fill=255)
        
        # Current program
        program = self.led_controller.current_program.capitalize()
        self.draw.text((2, 12), f"Mode: {program}", font=self.small_font, fill=255)
        
        # FPS
        fps = self.led_controller.stats.get('fps', 0)
        self.draw.text((2, 22), f"FPS: {fps}", font=self.small_font, fill=255)
        
        # Brightness
        brightness = int(self.led_controller.config.BRIGHTNESS * 100)
        self.draw.text((64, 22), f"Bright: {brightness}%", font=self.small_font, fill=255)
        
        # Speed
        speed = self.led_controller.config.SPEED
        self.draw.text((2, 32), f"Speed: {speed}x", font=self.small_font, fill=255)
        
        # Palette
        palette = self.led_controller.config.CURRENT_PALETTE
        self.draw.text((64, 32), f"Pal: {palette[:6]}", font=self.small_font, fill=255)
        
        # Uptime
        uptime = self.led_controller.stats.get('uptime', 0)
        uptime_str = self.format_uptime(uptime)
        self.draw.text((2, 42), f"Uptime: {uptime_str}", font=self.small_font, fill=255)
        
        # Frame count (abbreviated)
        frames = self.led_controller.stats.get('frame_count', 0)
        if frames > 1000000:
            frame_str = f"{frames // 1000000}M"
        elif frames > 1000:
            frame_str = f"{frames // 1000}K"
        else:
            frame_str = str(frames)
        self.draw.text((2, 52), f"Frames: {frame_str}", font=self.small_font, fill=255)
        
        # Progress bar for brightness
        bar_width = 60
        bar_height = 4
        bar_x = 64
        bar_y = 54
        self.draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), outline=255, fill=0)
        fill_width = int(bar_width * self.led_controller.config.BRIGHTNESS)
        if fill_width > 0:
            self.draw.rectangle((bar_x, bar_y, bar_x + fill_width, bar_y + bar_height), outline=255, fill=255)
        
        # Display image
        self.display.image(self.image)
        self.display.show()
        
    def format_uptime(self, seconds):
        """Format uptime nicely"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h{minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d{hours}h"
            
    def show_message(self, message, duration=2):
        """Show a temporary message on the display"""
        if not self.display:
            return
            
        # Clear and show message
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        
        # Center the message
        bbox = self.draw.textbbox((0, 0), message, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        
        self.draw.text((x, y), message, font=self.font, fill=255)
        
        self.display.image(self.image)
        self.display.show()
        
        # Schedule return to normal display
        if duration > 0:
            threading.Timer(duration, self.update_display).start()
            
    def show_startup_animation(self):
        """Show a startup animation"""
        if not self.display:
            return
            
        # Simple expanding box animation
        for i in range(0, min(self.width, self.height) // 2, 2):
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            self.draw.rectangle(
                (self.width//2 - i, self.height//2 - i, 
                 self.width//2 + i, self.height//2 + i),
                outline=255, fill=0
            )
            self.display.image(self.image)
            self.display.show()
            time.sleep(0.02)
            
        self.show_message("LightBox", duration=1)