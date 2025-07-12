"""
Unified animation controller with performance optimizations.
Consolidates the best features from all conductor implementations.
"""

import time
import threading
import signal
import sys
import os
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Callable

from .config import ConfigManager
from .performance import PerformanceMonitor, FrameRateLimiter, FrameBufferPool

# Use absolute imports when running as main module
try:
    from ..drivers.matrix_driver import create_matrix_driver
    from ..hardware.hardware_manager import HardwareManager
except ImportError:
    # Fallback for when running as main script
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from drivers.matrix_driver import create_matrix_driver
    from hardware.hardware_manager import HardwareManager

logger = logging.getLogger(__name__)


class AnimationProgram:
    """Wrapper for animation programs."""
    
    def __init__(self, name: str, animate_func: Callable, params: Optional[Dict] = None):
        self.name = name
        self.animate = animate_func
        self.params = params or {}
        self.frame_count = 0
    
    def reset(self):
        """Reset animation state."""
        self.frame_count = 0


class Conductor:
    """Unified animation controller with performance optimizations."""
    
    def __init__(self, config_path: str = "settings.json"):
        # Core components
        self.config = ConfigManager(config_path)
        self.performance = PerformanceMonitor(
            stats_interval=self.config.get("performance.stats_interval", 10)
        )
        self.matrix = None
        self.hardware = None
        
        # Animation management
        self.animations = {}
        self.current_animation = None
        self._animation_lock = threading.Lock()
        
        # Performance optimizations
        self._frame_pool = FrameBufferPool(
            size=self.config.get("performance.buffer_pool_size", 3),
            pixels=self._get_pixel_count()
        )
        self._frame_limiter = FrameRateLimiter(
            target_fps=self.config.get("target_fps", 30)
        )
        
        # Control flags
        self.running = False
        self._paused = False
        
        # Web server reference
        self.web_server = None
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Conductor initialized for {self.config.platform} platform")
    
    def _get_pixel_count(self) -> int:
        """Get total pixel count based on configuration."""
        if self.config.get("matrix_type") == "hub75":
            cols = self.config.get("hub75.cols", 64)
            rows = self.config.get("hub75.rows", 64)
            return cols * rows
        else:
            return self.config.get("ws2811.num_pixels", 100)
    
    def initialize(self) -> bool:
        """Initialize all hardware components."""
        try:
            # Create matrix driver
            self.matrix = create_matrix_driver(self.config)
            if not self.matrix.initialize():
                logger.error("Failed to initialize matrix driver")
                return False
            
            # Initialize hardware manager
            self.hardware = HardwareManager(self.config, self)
            
            # Load animations
            self._load_animations()
            
            # Set initial animation
            default_animation = self.config.get("animation_program", "cosmic")
            self.set_animation(default_animation)
            
            logger.info("Conductor initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def _load_animations(self):
        """Load all available animation programs."""
        # Built-in cosmic animation
        try:
            # Try absolute import first
            from animations.cosmic import animate as cosmic_animate
            self.animations["cosmic"] = AnimationProgram("cosmic", cosmic_animate)
        except ImportError:
            try:
                # Try relative import
                from ..animations.cosmic import animate as cosmic_animate
                self.animations["cosmic"] = AnimationProgram("cosmic", cosmic_animate)
            except ImportError:
                # Load from file as fallback
                cosmic_path = Path(__file__).parent.parent / "animations" / "cosmic.py"
                if cosmic_path.exists():
                    spec = importlib.util.spec_from_file_location("cosmic", cosmic_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'animate'):
                        self.animations["cosmic"] = AnimationProgram("cosmic", module.animate)
                else:
                    logger.warning("Could not load built-in cosmic animation")
        
        # Load animations from scripts directory
        scripts_dirs = [
            Path("scripts"),
            Path("animations"),
            Path("LightBox/scripts"),
            Path("LightBox/animations")
        ]
        
        for scripts_dir in scripts_dirs:
            if scripts_dir.exists():
                self._load_animations_from_directory(scripts_dir)
        
        logger.info(f"Loaded {len(self.animations)} animations")
    
    def _load_animations_from_directory(self, directory: Path):
        """Load animation scripts from a directory."""
        for script_path in directory.glob("*.py"):
            if script_path.name.startswith("_"):
                continue
                
            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(
                    script_path.stem,
                    script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check for animate function
                if hasattr(module, 'animate'):
                    # Get parameters if defined
                    params = getattr(module, 'PARAMS', {})
                    
                    self.animations[script_path.stem] = AnimationProgram(
                        script_path.stem,
                        module.animate,
                        params
                    )
                    logger.debug(f"Loaded animation: {script_path.stem}")
                    
            except Exception as e:
                logger.error(f"Failed to load animation {script_path}: {e}")
    
    def set_animation(self, name: str) -> bool:
        """Set the current animation program."""
        with self._animation_lock:
            if name not in self.animations:
                logger.error(f"Animation not found: {name}")
                return False
            
            self.current_animation = self.animations[name]
            self.current_animation.reset()
            self.config.set("animation_program", name)
            
            logger.info(f"Set animation: {name}")
            return True
    
    def run(self):
        """Main animation loop with frame rate control."""
        if not self.matrix:
            logger.error("Matrix not initialized")
            return
        
        self.running = True
        logger.info("Starting animation loop")
        
        # Get frame buffer from pool
        pixels = [(0, 0, 0)] * self.matrix.num_pixels
        
        while self.running:
            try:
                # Start frame timing
                self.performance.frame_start()
                
                if not self._paused and self.current_animation:
                    # Run animation
                    self.current_animation.animate(
                        pixels,
                        self.config,
                        self.current_animation.frame_count
                    )
                    self.current_animation.frame_count += 1
                    
                    # Update matrix
                    self.matrix.update(pixels)
                
                # Frame rate limiting
                self._frame_limiter.limit()
                
                # Update performance metrics
                self.performance.frame_end()
                
                # Process hardware events
                if self.hardware:
                    self.hardware.process_events()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Animation error: {e}")
                time.sleep(0.1)  # Prevent tight error loop
        
        logger.info("Animation loop stopped")
    
    def pause(self):
        """Pause animation."""
        self._paused = True
        logger.info("Animation paused")
    
    def resume(self):
        """Resume animation."""
        self._paused = False
        logger.info("Animation resumed")
    
    def stop(self):
        """Stop the conductor."""
        logger.info("Stopping conductor...")
        self.running = False
        
        # Stop web server if running
        if self.web_server:
            self.web_server.stop()
        
        # Clean up hardware
        if self.hardware:
            self.hardware.cleanup()
        
        # Clean up matrix
        if self.matrix:
            self.matrix.cleanup()
        
        # Save configuration
        self.config.cleanup()
        
        # Log final stats
        self.performance.log_stats()
        self.performance.cleanup()
        
        logger.info("Conductor stopped")
    
    def _signal_handler(self, signum, _frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def set_brightness(self, brightness: float):
        """Set matrix brightness."""
        brightness = max(0.0, min(1.0, brightness))
        self.config.set("brightness", brightness)
        
        if self.matrix:
            self.matrix.set_brightness(brightness)
    
    def set_speed(self, speed: float):
        """Set animation speed."""
        speed = max(0.1, min(10.0, speed))
        self.config.set("speed", speed)
    
    def set_palette(self, palette: str):
        """Set color palette."""
        self.config.set("color_palette", palette)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "running": self.running,
            "paused": self._paused,
            "animation": self.current_animation.name if self.current_animation else None,
            "brightness": self.config.get("brightness"),
            "speed": self.config.get("speed"),
            "palette": self.config.get("color_palette"),
            "platform": self.config.platform,
            "matrix_type": self.config.get("matrix_type"),
            "performance": self.performance.get_stats(),
            "animations": list(self.animations.keys())
        }
    
    def save_preset(self, name: str):
        """Save current settings as preset."""
        self.config.save_preset(name)
    
    def load_preset(self, name: str) -> bool:
        """Load settings from preset."""
        return self.config.load_preset(name)



    def reset_animation(self) -> bool:
        """Reset the current animation to its initial state."""
        with self._animation_lock:
            if self.current_animation:
                self.current_animation.reset()
                logger.info(f"Reset animation: {self.current_animation.name}")
                return True
            return False
    
    def clear_caches(self):
        """Clear all performance caches."""
        # Clear config caches
        self.config._color_cache.clear()
        
        # Clear any other caches
        logger.info("Cleared all caches")
    
    def emergency_stop(self):
        """Emergency stop - immediately halt all operations."""
        logger.warning("Emergency stop triggered!")
        self.stop()
        
        # Turn off all LEDs
        if self.matrix:
            try:
                self.matrix.clear()
                self.matrix.show()
            except Exception as e:
                logger.error(f"Error clearing matrix during emergency stop: {e}")
    

def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create conductor
    conductor = Conductor()
    
    # Initialize hardware
    if not conductor.initialize():
        logger.error("Failed to initialize conductor")
        return 1
    
    # Optional: Start web server
    if conductor.config.get("enable_web", True):
        try:
            try:
                from ..web.app import create_app, run_server
            except ImportError:
                # Fallback for when running as main script
                from web.app import create_app, run_server
            app = create_app(conductor)
            
            # Run web server in background thread
            web_thread = threading.Thread(
                target=run_server,
                args=(app,),
                kwargs={
                    'host': conductor.config.get("web.host", "0.0.0.0"),
                    'port': conductor.config.get("web.port", 5001)
                },
                daemon=True
            )
            web_thread.start()
            logger.info("Web interface started")
        except Exception as e:
            logger.warning(f"Web interface not available: {e}")
    
    # Run animation loop
    try:
        conductor.run()
    finally:
        conductor.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())