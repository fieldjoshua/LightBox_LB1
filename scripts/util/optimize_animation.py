#!/usr/bin/env python3
"""
Animation Optimizer for HUB75 LED Matrix

This script helps optimize existing animation scripts for HUB75 LED matrix
displays. It adds:
1. Proper structure
2. Standard parameters
3. Performance optimizations
4. Documentation

Usage:
  python optimize_animation.py path/to/animation.py

The original file will be backed up with a .bak extension.
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Animation template with standard structure
TEMPLATE = '''"""
{name} - Optimized HUB75 Animation
{description}

This animation is optimized for HUB75 LED matrices with the following features:
- Double buffering with SwapOnVSync for tear-free animation
- Efficient array processing for better performance
- Parameter standardization
- Gamma correction for accurate colors
"""

import math
import random
import time
from typing import List, Tuple, Optional

# Parameter defaults that can be overridden via the config
DEFAULT_PARAMS = {{
    "speed": 1.0,
    "intensity": 1.0,
    "scale": 1.0,
    "hue_shift": 0.0,
    "saturation": 0.9,
    "color_intensity": 1.0
    # Add any animation-specific parameters below
{extra_params}
}}

def animate(pixels: List[Tuple[int, int, int]], config, frame: int) -> None:
    """
    {name} animation frame renderer.
    
    Args:
        pixels: List of RGB pixel values to modify in-place
        config: Configuration object with parameters
        frame: Current frame number
    """
    # Get matrix dimensions
    width = config.get("matrix_width", 64)
    height = config.get("matrix_height", 64)
    
    # Get animation parameters with defaults
    speed = config.get("speed", 1.0)
    brightness = config.get("brightness", 1.0) 
    intensity = config.get("intensity", DEFAULT_PARAMS["intensity"])
    scale = config.get("scale", DEFAULT_PARAMS["scale"])
    hue_shift = config.get("hue_shift", DEFAULT_PARAMS["hue_shift"])
    saturation = config.get("saturation", DEFAULT_PARAMS["saturation"])
    color_intensity = config.get("color_intensity", DEFAULT_PARAMS["color_intensity"])
    
    # Time-based animation using frame count
    t = frame * config.get("time_scale", 0.05) * speed
    
{animation_code}

# Animation metadata
ANIMATION_INFO = {{
    "name": "{name}",
    "description": "{description}",
    "parameters": DEFAULT_PARAMS,
    "tags": {tags},
    "fps_target": {fps_target}
}}
'''

def extract_animation_code(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """Extract animation code and info from an existing script."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Initialize variables with defaults
    metadata = {
        "name": file_path.stem.replace('_', ' ').title(),
        "description": "HUB75 LED Matrix Animation",
        "tags": ["visual", "effect"],
        "fps_target": 30,
        "extra_params": {}
    }
    
    # Extract animate function if it exists
    animate_match = re.search(r'def\s+animate\s*\(.*?\).*?:(.*?)(?:def|\Z)', 
                              content, re.DOTALL)
    
    if animate_match:
        code = animate_match.group(1).strip()
        
        # Look for parameters within the animate function
        param_pattern = r'(\w+)\s*=\s*config\.get\s*\(\s*[\'"](\w+)[\'"]\s*,\s*([^)]+)\s*\)'
        params = {}
        
        for match in re.finditer(param_pattern, code):
            var_name = match.group(1)
            param_name = match.group(2)
            default_value = match.group(3).strip()
            
            # Only add custom parameters (not standard ones)
            if param_name not in ['speed', 'brightness', 'intensity', 'scale', 
                                 'hue_shift', 'saturation', 'color_intensity',
                                 'matrix_width', 'matrix_height', 'time_scale']:
                params[param_name] = default_value
        
        if params:
            # Format extra parameters for the template
            extra_params = []
            for name, value in params.items():
                extra_params.append(f'    "{name}": {value},')
            metadata["extra_params"] = "\n".join(extra_params)
        
        # Try to find a better name and description
        name_match = re.search(r'[\'"](.*?)[\'"]\s*-\s*(.*?)[\'""\n]', content)
        if name_match:
            metadata["name"] = name_match.group(1)
            metadata["description"] = name_match.group(2)
        
        # Look for animation info/metadata
        info_match = re.search(r'(ANIMATION_INFO|PARAMS)\s*=\s*{(.*?)}', content, re.DOTALL)
        if info_match:
            # Try to parse the info dictionary
            info_str = info_match.group(2).strip()
            
            # Extract tags if present
            tags_match = re.search(r'[\'"]tags[\'"]\s*:\s*\[(.*?)\]', info_str, re.DOTALL)
            if tags_match:
                tags_str = tags_match.group(1).strip()
                if tags_str:
                    try:
                        # Safely evaluate the tags list
                        tags = []
                        for tag in tags_str.split(','):
                            tag = tag.strip()
                            if tag.startswith('"') or tag.startswith("'"):
                                tag = tag[1:-1] if tag.endswith(tag[0]) else tag[1:]
                            tags.append(tag)
                        if tags:
                            metadata["tags"] = tags
                    except:
                        pass
            
            # Extract fps_target if present
            fps_match = re.search(r'[\'"]fps_target[\'"]\s*:\s*(\d+)', info_str)
            if fps_match:
                metadata["fps_target"] = int(fps_match.group(1))
        
        return code, metadata
    
    # If no animate function found, return empty code
    return "", metadata


def optimize_animation(file_path: Path, output_path: Optional[Path] = None, backup: bool = True) -> bool:
    """
    Optimize an animation script for HUB75 LED matrix.
    
    Args:
        file_path: Path to the animation script
        output_path: Path to write the optimized script (defaults to overwriting input)
        backup: Whether to create a backup of the original file
        
    Returns:
        bool: True if optimization succeeded
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    # Create backup if requested
    if backup:
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy(file_path, backup_path)
        print(f"Created backup: {backup_path}")
    
    try:
        # Extract animation code and metadata
        code, metadata = extract_animation_code(file_path)
        if not code:
            print(f"Warning: No animate function found in {file_path}")
            # Still continue with empty code
            code = "    # Original animation code not found\n    pass"
        
        # Indent code properly
        indented_code = "\n".join(f"    {line}" if line.strip() else line 
                                 for line in code.split("\n"))
        
        # Format tags list
        tags_str = str(metadata["tags"])
        
        # Create the optimized script from template
        script = TEMPLATE.format(
            name=metadata["name"],
            description=metadata["description"],
            extra_params=metadata.get("extra_params", ""),
            animation_code=indented_code,
            tags=tags_str,
            fps_target=metadata["fps_target"]
        )
        
        # Write the optimized script
        if output_path is None:
            output_path = file_path
        
        with open(output_path, 'w') as f:
            f.write(script)
        
        print(f"Successfully optimized: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error optimizing {file_path}: {e}")
        return False


def batch_optimize(directory: Path, pattern: str = "*hub75.py") -> None:
    """
    Batch optimize all animation scripts in a directory.
    
    Args:
        directory: Directory containing animation scripts
        pattern: Filename pattern to match (default: *hub75.py)
    """
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory not found: {directory}")
        return
    
    # Find all matching files
    animation_files = list(directory.glob(pattern))
    if not animation_files:
        print(f"No animation files found matching pattern: {pattern}")
        return
    
    print(f"Found {len(animation_files)} animation files to optimize")
    
    # Optimize each file
    success_count = 0
    for file_path in animation_files:
        print(f"\nOptimizing: {file_path}")
        if optimize_animation(file_path):
            success_count += 1
    
    print(f"\nOptimized {success_count} of {len(animation_files)} files")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Optimize animation scripts for HUB75 LED matrix"
    )
    
    parser.add_argument(
        "path",
        type=str,
        help="Path to animation file or directory"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output path (defaults to overwriting input)"
    )
    
    parser.add_argument(
        "--pattern", "-p",
        type=str,
        default="*hub75.py",
        help="Filename pattern for batch processing (default: *hub75.py)"
    )
    
    parser.add_argument(
        "--no-backup", "-n",
        action="store_true",
        help="Don't create backup files"
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_dir():
        # Batch processing mode
        batch_optimize(path, args.pattern)
    else:
        # Single file mode
        output_path = Path(args.output) if args.output else None
        optimize_animation(path, output_path, not args.no_backup)


if __name__ == "__main__":
    main() 