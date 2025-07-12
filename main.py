#!/usr/bin/env python3
"""
LightBox Organized - Main Entry Point
Unified HUB75 LED Matrix Controller with Web GUI

This is the main entry point that integrates all the building blocks:
- Core animation conductor
- HUB75 hardware driver with Zeller optimizations
- Web GUI for real-time control
- Hardware management (buttons, OLED)
- Performance monitoring and optimization
"""

import signal
import sys
import threading
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import core components
from core.conductor import Conductor
from core.config import ConfigManager
from web.app import create_app
from hardware.hardware_manager import HardwareManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lightbox.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class LightBoxController:
    """Main LightBox controller that orchestrates all components."""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config = ConfigManager(config_path)
        self.conductor = None
        self.web_app = None
        self.hardware_manager = None
        self.running = False
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("LightBox Controller initialized")
    
    def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("Initializing LightBox system...")
            
            # Initialize conductor (animation engine)
            self.conductor = Conductor(self.config.config_path)
            if not self.conductor.initialize():
                logger.error("Failed to initialize conductor")
                return False
            
            # Initialize hardware manager
            self.hardware_manager = HardwareManager(
                self.config, self.conductor
            )
            
            # Initialize web application
            self.web_app = create_app(self.conductor)
            self.conductor.web_server = self.web_app
            
            logger.info("LightBox system initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def start(self):
        """Start the LightBox system."""
        if not self.initialize():
            logger.error("Failed to initialize system")
            return False
        
        try:
            self.running = True
            logger.info("Starting LightBox system...")
            
            # Start conductor in background thread
            conductor_thread = threading.Thread(
                target=self.conductor.run,
                daemon=True
            )
            conductor_thread.start()
            
            # Start web server
            port = self.config.get("web.port", 5000)
            host = self.config.get("web.host", "0.0.0.0")
            debug = self.config.get("web.debug", False)
            
            logger.info(f"Starting web server on {host}:{port}")
            self.web_app.socketio.run(
                self.web_app,
                host=host,
                port=port,
                debug=debug,
                use_reloader=False
            )
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error during execution: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the LightBox system."""
        logger.info("Stopping LightBox system...")
        self.running = False
        
        if self.conductor:
            self.conductor.stop()
        
        if self.hardware_manager:
            self.hardware_manager.cleanup()
        
        logger.info("LightBox system stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point."""
    print("=" * 50)
    print("LightBox Organized - HUB75 LED Matrix Controller")
    print("=" * 50)
    
    # Create and start controller
    controller = LightBoxController()
    controller.start()


if __name__ == "__main__":
    main() 