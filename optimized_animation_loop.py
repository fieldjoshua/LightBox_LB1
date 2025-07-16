"""
Optimized Animation Loop - 120 FPS Capable
==========================================

Fixes the hardcoded 20 FPS limit and implements proper double buffering.
"""

import time
import threading
from typing import Dict, Any

class OptimizedAnimationLoop:
    """120 FPS capable animation loop with proper double buffering"""
    
    def __init__(self, matrix_controller, target_fps=120):
        self.matrix = matrix_controller
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps  # 0.0083s for 120 FPS
        
        self.running = False
        self.current_animation = None
        self.frame_count = 0
        
        # Performance optimization
        self.pixels = [(0, 0, 0)] * (64 * 64)
        
    def _animation_loop(self):
        """Main animation loop with precise 120 FPS timing"""
        
        while self.running:
            frame_start = time.perf_counter()
            
            if self.current_animation:
                # Run animation (optimized versions)
                self.current_animation(self.pixels, {}, self.frame_count)
                
                # OPTIMIZED RENDERING: Use double buffering instead of SetPixel
                if hasattr(self.matrix, 'CreateFrameCanvas'):
                    # Modern double buffering approach
                    canvas = self.matrix.CreateFrameCanvas()
                    
                    for y in range(64):
                        for x in range(64):
                            idx = y * 64 + x
                            if idx < len(self.pixels):
                                r, g, b = self.pixels[idx]
                                canvas.SetPixel(x, y, r, g, b)
                    
                    # Tear-free swap - this is the key optimization!
                    self.matrix.SwapOnVSync(canvas)
                else:
                    # Fallback for systems without double buffering
                    self.matrix.Clear()
                    for y in range(64):
                        for x in range(64):
                            idx = y * 64 + x
                            if idx < len(self.pixels):
                                r, g, b = self.pixels[idx]
                                self.matrix.SetPixel(x, y, r, g, b)
                
                self.frame_count += 1
            
            # CRITICAL: Precise frame timing for 120 FPS
            elapsed = time.perf_counter() - frame_start
            sleep_time = self.frame_time - elapsed
            
            if sleep_time > 0:
                # High-precision timing
                if sleep_time > 0.001:  # 1ms
                    time.sleep(sleep_time - 0.0005)  # Sleep most of it
                
                # Busy wait for final precision
                while time.perf_counter() - frame_start < self.frame_time:
                    pass
            
    def start(self):
        """Start the optimized animation loop"""
        self.running = True
        threading.Thread(target=self._animation_loop, daemon=True).start()
        print(f"✅ Optimized animation loop started at {self.target_fps} FPS")
    
    def stop(self):
        """Stop animation loop"""
        self.running = False
