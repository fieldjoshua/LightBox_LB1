"""
Performance monitoring and optimization utilities.
Provides metrics collection with minimal overhead.
"""

import time
import threading
import json
import os
from collections import deque
from typing import Dict, Optional, Any
import logging

# Try to import psutil, but make it optional
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Provide a dummy Process class for compatibility
    class DummyProcess:
        def cpu_percent(self, interval=None):
            return 0.0
        
        def memory_info(self):
            class MemInfo:
                rss = 0
            return MemInfo()
    
    class psutil:
        @staticmethod
        def Process():
            return DummyProcess()

logger = logging.getLogger(__name__)


class RollingAverage:
    """Efficient rolling average calculator."""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self._sum = 0.0
        self._lock = threading.Lock()
    
    def add(self, value: float):
        """Add a value to the rolling average."""
        with self._lock:
            if len(self.values) == self.window_size:
                # Remove oldest value from sum
                self._sum -= self.values[0]
            
            self.values.append(value)
            self._sum += value
    
    @property
    def average(self) -> float:
        """Get the current average."""
        with self._lock:
            if not self.values:
                return 0.0
            return self._sum / len(self.values)
    
    @property
    def current(self) -> float:
        """Get the most recent value."""
        with self._lock:
            return self.values[-1] if self.values else 0.0
    
    def reset(self):
        """Reset the rolling average."""
        with self._lock:
            self.values.clear()
            self._sum = 0.0


class PerformanceMonitor:
    """System performance tracking with minimal overhead."""
    
    def __init__(self, stats_interval: int = 10):
        """Initialize performance monitor.
        
        Args:
            stats_interval: Interval for logging stats (seconds)
        """
        self.start_time = time.time()
        self.frame_count = 0
        self.frame_times = deque(maxlen=100)
        self.render_times = deque(maxlen=100)
        self.stats_interval = stats_interval
        self.last_stats_time = self.start_time
        self.frame_start_time = 0
        self.render_start_time = 0
        self.avg_frame_time = 0
        self.avg_render_time = 0
        self.fps = 0.0  # Initialize fps attribute
        
        # CPU and memory monitoring
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.last_cpu_check = self.start_time
        
        self.metrics = {
            'fps': RollingAverage(30),
            'frame_time_ms': RollingAverage(30),
            'cpu_percent': RollingAverage(10),
            'memory_mb': RollingAverage(10),
            'dropped_frames': 0,
            'total_frames': 0
        }
        
        # Frame timing
        self._last_frame_time = time.perf_counter()
        self._frame_start_time = None
        
        # System metrics
        self._process = psutil.Process()
        self._last_stats_save = time.time()
        
        # Background metrics collection
        self._running = True
        self._metrics_thread = threading.Thread(
            target=self._collect_system_metrics,
            daemon=True
        )
        self._metrics_thread.start()
        
        logger.info("Performance monitor initialized")
    
    def frame_start(self):
        """Mark the start of a frame."""
        self._frame_start_time = time.perf_counter()
    
    def frame_end(self):
        """Mark the end of a frame and update metrics."""
        if self._frame_start_time is None:
            return
            
        current_time = time.perf_counter()
        frame_time = current_time - self._frame_start_time
        
        # Update frame metrics
        self.metrics['frame_time_ms'].add(frame_time * 1000)
        self.metrics['fps'].add(1.0 / frame_time if frame_time > 0 else 0)
        self.metrics['total_frames'] += 1
        
        # Check for dropped frames (>33ms for 30 FPS target)
        if frame_time > 0.033:
            self.metrics['dropped_frames'] += 1
        
        self._last_frame_time = current_time
        self._frame_start_time = None
    
    def update(self, frame_time: float):
        """Update metrics with frame time (alternative to frame_start/end)."""
        self.metrics['frame_time_ms'].add(frame_time * 1000)
        self.metrics['fps'].add(1.0 / frame_time if frame_time > 0 else 0)
        self.metrics['total_frames'] += 1
        
        # Check for dropped frames
        if frame_time > 0.033:  # 30 FPS target
            self.metrics['dropped_frames'] += 1
    
    def _collect_system_metrics(self):
        """Background thread to collect system metrics."""
        while self._running:
            try:
                # CPU usage (non-blocking)
                cpu_percent = self._process.cpu_percent(interval=None)
                self.metrics['cpu_percent'].add(cpu_percent)
                
                # Memory usage
                memory_info = self._process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                self.metrics['memory_mb'].add(memory_mb)
                
                # Save stats periodically
                if time.time() - self._last_stats_save > self.stats_interval:
                    self._save_stats()
                    self._last_stats_save = time.time()
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            # Sleep for 1 second between collections
            time.sleep(1.0)
    
    def _save_stats(self):
        """Save performance statistics to file."""
        stats = self.get_stats()
        
        try:
            stats_file = f'/tmp/lightbox_stats_{os.getpid()}.json'
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'fps': {
                'current': self.metrics['fps'].current,
                'average': self.metrics['fps'].average
            },
            'frame_time_ms': {
                'current': self.metrics['frame_time_ms'].current,
                'average': self.metrics['frame_time_ms'].average
            },
            'cpu_percent': {
                'current': self.metrics['cpu_percent'].current,
                'average': self.metrics['cpu_percent'].average
            },
            'memory_mb': {
                'current': self.metrics['memory_mb'].current,
                'average': self.metrics['memory_mb'].average
            },
            'dropped_frames': self.metrics['dropped_frames'],
            'total_frames': self.metrics['total_frames'],
            'drop_rate': (self.metrics['dropped_frames'] / 
                         max(1, self.metrics['total_frames'])) * 100
        }
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.metrics['fps'].average
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return self.metrics['cpu_percent'].average
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.metrics['memory_mb'].average
    
    def get_metrics(self) -> dict:
        """Get all performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        return {
            "fps": self.get_fps(),
            "frame_count": self.metrics['total_frames'],
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "uptime": time.time() - self.start_time,
            "render_time": self.metrics['frame_time_ms'].average / 1000.0,
            "frame_time": self.metrics['frame_time_ms'].average / 1000.0
        }
    
    def log_stats(self):
        """Log current performance statistics."""
        stats = self.get_stats()
        logger.info(
            f"Performance: {stats['fps']['average']:.1f} FPS, "
            f"Frame time: {stats['frame_time_ms']['average']:.1f}ms, "
            f"CPU: {stats['cpu_percent']['average']:.1f}%, "
            f"Memory: {stats['memory_mb']['average']:.1f}MB, "
            f"Dropped: {stats['drop_rate']:.1f}%"
        )
    
    def cleanup(self):
        """Clean up resources."""
        self._running = False
        if self._metrics_thread.is_alive():
            self._metrics_thread.join(timeout=2.0)


class FrameRateLimiter:
    """Precise frame rate limiting for consistent timing."""
    
    def __init__(self, target_fps: float):
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / target_fps
        self._last_frame_time = time.perf_counter()
        self._sleep_precision = 0.001  # 1ms precision
    
    def limit(self):
        """Sleep to maintain target frame rate."""
        current_time = time.perf_counter()
        elapsed = current_time - self._last_frame_time
        
        if elapsed < self.target_frame_time:
            # Calculate sleep time
            sleep_time = self.target_frame_time - elapsed
            
            # Use precise sleeping for better accuracy
            if sleep_time > self._sleep_precision:
                time.sleep(sleep_time - self._sleep_precision)
            
            # Busy wait for the remaining time
            while time.perf_counter() - self._last_frame_time < self.target_frame_time:
                pass
        
        self._last_frame_time = time.perf_counter()
    
    def reset(self):
        """Reset the frame timer."""
        self._last_frame_time = time.perf_counter()


class FrameBufferPool:
    """Object pool for frame buffers to reduce allocations."""
    
    def __init__(self, size: int = 3, pixels: int = 4096):
        self._pool = deque(maxlen=size)
        self._pixels = pixels
        self._lock = threading.Lock()
        
        # Pre-allocate buffers
        for _ in range(size):
            buffer = bytearray(pixels * 3)  # RGB bytes
            self._pool.append(buffer)
        
        logger.info(f"Frame buffer pool initialized with {size} buffers")
    
    def acquire(self) -> bytearray:
        """Get a frame buffer from pool."""
        with self._lock:
            if self._pool:
                return self._pool.popleft()
            else:
                # Create new buffer if pool is empty
                logger.warning("Frame buffer pool exhausted, creating new buffer")
                return bytearray(self._pixels * 3)
    
    def release(self, buffer: bytearray):
        """Return frame buffer to pool."""
        with self._lock:
            # Clear buffer before returning to pool
            buffer[:] = b'\x00' * len(buffer)
            
            if len(self._pool) < self._pool.maxlen:
                self._pool.append(buffer)


class MathCache:
    """Cached mathematical operations for animations."""
    
    def __init__(self, cache_size: int = 1000):
        self._sin_cache = {}
        self._cos_cache = {}
        self._cache_size = cache_size
        self._precision = 3  # Decimal places for cache keys
    
    def sin(self, angle: float) -> float:
        """Cached sine calculation."""
        import math
        
        # Round to precision for cache key
        key = round(angle, self._precision)
        
        if key not in self._sin_cache:
            # Limit cache size
            if len(self._sin_cache) >= self._cache_size:
                # Remove oldest entry (simple FIFO)
                self._sin_cache.pop(next(iter(self._sin_cache)))
            
            self._sin_cache[key] = math.sin(angle)
        
        return self._sin_cache[key]
    
    def cos(self, angle: float) -> float:
        """Cached cosine calculation."""
        import math
        
        key = round(angle, self._precision)
        
        if key not in self._cos_cache:
            if len(self._cos_cache) >= self._cache_size:
                self._cos_cache.pop(next(iter(self._cos_cache)))
            
            self._cos_cache[key] = math.cos(angle)
        
        return self._cos_cache[key]
    
    def clear(self):
        """Clear all caches."""
        self._sin_cache.clear()
        self._cos_cache.clear()