"""
Frame buffer utilities for LightBox.
"""



class FrameBuffer:
    """Frame buffer for LED matrix operations."""

    def __init__(self, width: int, height: int, fill_color: tuple[int, int, int] = (0, 0, 0)):
        """Initialize frame buffer.
        
        Args:
            width: Buffer width
            height: Buffer height
            fill_color: Initial fill color
        """
        self.width = width
        self.height = height
        self.pixels = [fill_color] * (width * height)

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        """Set pixel at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: RGB color tuple
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = color

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int]:
        """Get pixel color at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            RGB color tuple
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y * self.width + x]
        return (0, 0, 0)

    def fill(self, color: tuple[int, int, int]) -> None:
        """Fill entire buffer with color.
        
        Args:
            color: RGB color tuple
        """
        self.pixels = [color] * (self.width * self.height)

    def clear(self) -> None:
        """Clear buffer to black."""
        self.pixels = [(0, 0, 0)] * (self.width * self.height)

    def copy_from(self, other: 'FrameBuffer') -> None:
        """Copy pixels from another buffer.
        
        Args:
            other: Source frame buffer
        """
        if self.width == other.width and self.height == other.height:
            self.pixels = other.pixels.copy()

    def get_raw(self) -> list[tuple[int, int, int]]:
        """Get raw pixel data.
        
        Returns:
            List of RGB tuples
        """
        return self.pixels

    def set_raw(self, pixels: list[tuple[int, int, int]]) -> None:
        """Set raw pixel data.
        
        Args:
            pixels: List of RGB tuples
        """
        if len(pixels) == len(self.pixels):
            self.pixels = pixels.copy()


def create_frame(width: int, height: int,
                fill_color: tuple[int, int, int] = (0, 0, 0)) -> list[tuple[int, int, int]]:
    """Create a new frame buffer.
    
    Args:
        width: Buffer width
        height: Buffer height
        fill_color: Initial fill color
        
    Returns:
        List of RGB tuples
    """
    return [fill_color] * (width * height)
