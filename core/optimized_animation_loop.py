"""
Improved Animation Loop
======================

This loop fixes the timing and double buffering issues identified in the audit.
"""

import time
import threading
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class OptimizedAnimationLoop:
    """Animation loop with precise timing and double buffering"""
    
    def __init__(self, matrix_controller, target_fps=30):
        self.matrix = matrix_controller
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        
        self.running = False
        self.paused = False
        self.current_animation = None
        self.animation_params = {}
        
        self.frame_count = 0
        self._loop_thread = None
        
        # Timing precision
        self._last_frame_time = 0
        self._frame_stats = []
    
    def set_animation(self, animation_func, params=None):
        """Set current animation function"""
        self.current_animation = animation_func
        self.animation_params = params or {}
        self.frame_count = 0
        logger.info(f"Animation set: {getattr(animation_func, '__name__', 'Unknown')}")
    
    def start(self):
        """Start animation loop"""
        if self.running:
            return
        
        self.running = True
        self._loop_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._loop_thread.start()
        logger.info(f"Animation loop started at {self.target_fps} FPS")
    
    def stop(self):
        """Stop animation loop"""
        self.running = False
        if self._loop_thread:
            self._loop_thread.join(timeout=1.0)
        logger.info("Animation loop stopped")
    
    def pause(self):
        """Pause animation"""
        self.paused = True
    
    def resume(self):
        """Resume animation"""
        self.paused = False
    
    def _animation_loop(self):
        """Main animation loop with precise timing"""
        self._last_frame_time = time.perf_counter()
        
        while self.running:
            try:
                frame_start = time.perf_counter()
                
                if not self.paused and self.current_animation:
                    # Create pixel buffer
                    width, height = self.matrix.get_dimensions()
                    pixels = [(0, 0, 0)] * (width * height)
                    
                    # Run animation
                    self.current_animation(pixels, self.animation_params, self.frame_count)
                    
                    # Render with double buffering
                    with self.matrix.render_frame() as canvas:
                        if canvas:
                            for y in range(height):
                                for x in range(width):
                                    idx = y * width + x
                                    if idx < len(pixels):
                                        r, g, b = pixels[idx]
                                        canvas.SetPixel(x, y, r, g, b)
                    
                    self.frame_count += 1
                
                # Precise frame timing
                self._maintain_framerate(frame_start)
                
            except Exception as e:
                logger.error(f"Animation loop error: {e}")
                time.sleep(0.1)  # Prevent tight error loop
    
    def _maintain_framerate(self, frame_start):
        """Maintain precise frame rate"""
        elapsed = time.perf_counter() - frame_start
        remaining = self.frame_time - elapsed
        
        if remaining > 0:
            # Split sleep for better precision
            if remaining > 0.002:  # 2ms
                time.sleep(remaining - 0.001)
            
            # Busy wait for final precision
            while time.perf_counter() - frame_start < self.frame_time:
                pass
        
        # Track frame timing stats
        actual_time = time.perf_counter() - frame_start
        self._frame_stats.append(actual_time)
        
        # Keep only recent stats
        if len(self._frame_stats) > 100:
            self._frame_stats = self._frame_stats[-50:]
    
    def get_stats(self):
        """Get timing statistics"""
        if not self._frame_stats:
            return {}
        
        avg_time = sum(self._frame_stats) / len(self._frame_stats)
        max_time = max(self._frame_stats)
        min_time = min(self._frame_stats)
        
        return {
            'target_fps': self.target_fps,
            'actual_fps': 1.0 / avg_time if avg_time > 0 else 0,
            'frame_time_avg': avg_time * 1000,  # ms
            'frame_time_max': max_time * 1000,  # ms
            'frame_time_min': min_time * 1000,  # ms
            'frame_count': self.frame_count
        }
