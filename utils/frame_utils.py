"""
Frame utility functions for LightBox.
Provides frame buffer management and manipulation utilities.
"""

from typing import List, Tuple, Optional, Any
import time
from collections import deque


class FrameBuffer:
    """
    Simple frame buffer for storing pixel data.
    """
    
    def __init__(self, size: int):
        """Initialize frame buffer with given size."""
        self.size = size
        self.pixels = [(0, 0, 0)] * size
        self.timestamp = time.time()
    
    def update(self, pixels: List[Tuple[int, int, int]]):
        """Update the frame buffer with new pixel data."""
        if len(pixels) == self.size:
            self.pixels = pixels.copy()
        else:
            # Resize if needed
            self.pixels = (pixels[:self.size] + [(0, 0, 0)] * self.size)[:self.size]
        self.timestamp = time.time()
    
    def get_age(self) -> float:
        """Get age of the frame in seconds."""
        return time.time() - self.timestamp
    
    def clear(self):
        """Clear the frame buffer to black."""
        self.pixels = [(0, 0, 0)] * self.size
        self.timestamp = time.time()


class FrameBufferPool:
    """
    Pool of reusable frame buffers to reduce memory allocation.
    """
    
    def __init__(self, size: int, max_buffers: int = 10):
        """Initialize frame buffer pool."""
        self.size = size
        self.max_buffers = max_buffers
        self.available = deque()
        self.in_use = set()
        
        # Pre-allocate some buffers
        for _ in range(min(3, max_buffers)):
            self.available.append(FrameBuffer(size))
    
    def acquire(self) -> FrameBuffer:
        """Acquire a frame buffer from the pool."""
        if self.available:
            buffer = self.available.popleft()
        else:
            buffer = FrameBuffer(self.size)
        
        self.in_use.add(buffer)
        buffer.clear()
        return buffer
    
    def release(self, buffer: FrameBuffer):
        """Release a frame buffer back to the pool."""
        if buffer in self.in_use:
            self.in_use.remove(buffer)
            if len(self.available) < self.max_buffers:
                self.available.append(buffer)


def create_frame(width: int, height: int, 
                 color: Tuple[int, int, int] = (0, 0, 0)) -> List[Tuple[int, int, int]]:
    """
    Create a new frame with specified dimensions and color.
    
    Args:
        width: Frame width
        height: Frame height
        color: Fill color (default black)
        
    Returns:
        List of pixel colors
    """
    return [color] * (width * height)


def copy_frame(source: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
    """
    Create a copy of a frame.
    
    Args:
        source: Source frame
        
    Returns:
        Copy of the frame
    """
    return source.copy()


def blend_frames(frame1: List[Tuple[int, int, int]], 
                 frame2: List[Tuple[int, int, int]], 
                 factor: float) -> List[Tuple[int, int, int]]:
    """
    Blend two frames together.
    
    Args:
        frame1: First frame
        frame2: Second frame
        factor: Blend factor (0.0 = frame1, 1.0 = frame2)
        
    Returns:
        Blended frame
    """
    factor = max(0.0, min(1.0, factor))
    result = []
    
    for i in range(min(len(frame1), len(frame2))):
        r1, g1, b1 = frame1[i]
        r2, g2, b2 = frame2[i]
        
        r = int(r1 * (1 - factor) + r2 * factor)
        g = int(g1 * (1 - factor) + g2 * factor)
        b = int(b1 * (1 - factor) + b2 * factor)
        
        result.append((r, g, b))
    
    return result


def apply_frame_brightness(frame: List[Tuple[int, int, int]], 
                          brightness: float) -> List[Tuple[int, int, int]]:
    """
    Apply brightness to an entire frame.
    
    Args:
        frame: Input frame
        brightness: Brightness factor (0.0-1.0)
        
    Returns:
        Brightness-adjusted frame
    """
    brightness = max(0.0, min(1.0, brightness))
    return [
        (int(r * brightness), int(g * brightness), int(b * brightness))
        for r, g, b in frame
    ]


def shift_frame(frame: List[Tuple[int, int, int]], 
                width: int, height: int,
                dx: int, dy: int,
                wrap: bool = True) -> List[Tuple[int, int, int]]:
    """
    Shift frame contents by dx, dy pixels.
    
    Args:
        frame: Input frame
        width: Frame width
        height: Frame height
        dx: Horizontal shift (positive = right)
        dy: Vertical shift (positive = down)
        wrap: Whether to wrap pixels around edges
        
    Returns:
        Shifted frame
    """
    result = [(0, 0, 0)] * len(frame)
    
    for y in range(height):
        for x in range(width):
            src_x = x - dx
            src_y = y - dy
            
            if wrap:
                src_x = src_x % width
                src_y = src_y % height
            
            if 0 <= src_x < width and 0 <= src_y < height:
                src_idx = src_y * width + src_x
                dst_idx = y * width + x
                if 0 <= src_idx < len(frame) and 0 <= dst_idx < len(result):
                    result[dst_idx] = frame[src_idx]
    
    return result


def fade_frame(current: List[Tuple[int, int, int]], 
               target: List[Tuple[int, int, int]], 
               steps: int, 
               current_step: int) -> List[Tuple[int, int, int]]:
    """
    Fade from current frame to target frame over a number of steps.
    
    Args:
        current: Current frame
        target: Target frame
        steps: Total number of fade steps
        current_step: Current step (0 to steps-1)
        
    Returns:
        Frame at the current fade step
    """
    if steps <= 1 or current_step >= steps - 1:
        return target
    
    if current_step <= 0:
        return current
    
    factor = current_step / (steps - 1)
    return blend_frames(current, target, factor)


class FrameTransition:
    """
    Manages smooth transitions between frames.
    """
    
    def __init__(self, duration: float = 1.0):
        """
        Initialize frame transition.
        
        Args:
            duration: Transition duration in seconds
        """
        self.duration = duration
        self.start_frame: Optional[List[Tuple[int, int, int]]] = None
        self.end_frame: Optional[List[Tuple[int, int, int]]] = None
        self.start_time: Optional[float] = None
        self.active = False
    
    def start(self, current: List[Tuple[int, int, int]], 
              target: List[Tuple[int, int, int]]):
        """Start a new transition."""
        self.start_frame = copy_frame(current)
        self.end_frame = copy_frame(target)
        self.start_time = time.time()
        self.active = True
    
    def get_frame(self) -> Optional[List[Tuple[int, int, int]]]:
        """Get the current transition frame."""
        if not self.active or not self.start_time:
            return None
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.active = False
            return self.end_frame
        
        factor = elapsed / self.duration
        return blend_frames(self.start_frame, self.end_frame, factor)
    
    def is_active(self) -> bool:
        """Check if transition is active."""
        return self.active