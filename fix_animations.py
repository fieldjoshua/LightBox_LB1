#!/usr/bin/env python3
"""
Fix animation files with syntax errors (missing comma in parameter dictionaries)
"""

import os
import re
import glob

def fix_animation_file(file_path):
    """Fix the missing comma in the DEFAULT_PARAMS dictionary"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match dictionary with missing comma before a comment line
    pattern = r'(\s+)"([^"]+)":\s+([^,\n]+)(\s+)#'
    replacement = r'\1"\2": \3,\4#'
    
    # Apply the fix
    fixed_content = re.sub(pattern, replacement, content)
    
    # Only write if changes were made
    if fixed_content != content:
        print(f"Fixing {file_path}")
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        return True
    return False

def main():
    """Find and fix all animation files"""
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
    animation_files = glob.glob(os.path.join(script_dir, '*.py'))
    
    fixed_count = 0
    for file_path in animation_files:
        if fix_animation_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} animation files")

if __name__ == "__main__":
    main() 