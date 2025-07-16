#!/usr/bin/env python3
"""Debug script to test animation loading."""

import sys
import importlib.util
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from core.config import ConfigManager
from core.conductor import Conductor


def main():
    print("🔍 Debug Animation Loading")
    print("=" * 40)
    
    # Test config loading
    try:
        config = ConfigManager("config/settings.json")
        print("✅ Config loaded successfully")
        print(f"   Platform: {config.platform}")
        print(f"   Matrix type: {config.get('matrix_type')}")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False
    
    # Test conductor creation
    try:
        conductor = Conductor(config)
        print("✅ Conductor created successfully")
    except Exception as e:
        print(f"❌ Conductor creation failed: {e}")
        return False
    
    # Test conductor initialization
    try:
        success = conductor.initialize()
        print(f"✅ Conductor initialized: {success}")
    except Exception as e:
        print(f"❌ Conductor initialization failed: {e}")
        return False
    
    # Check animation loading
    print("\n🎬 Animation Status")
    print(f"   Animations loaded: {len(conductor.animations)}")
    print(f"   Available animations: {list(conductor.animations.keys())}")
    
    # Test individual animation scripts
    print("\n🔧 Testing individual scripts")
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        for script_path in scripts_dir.glob("*.py"):
            if script_path.name.startswith("_"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    script_path.stem,
                    script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                has_animate = hasattr(module, 'animate')
                has_params = hasattr(module, 'PARAMS') or \
                    hasattr(module, 'DEFAULT_PARAMS')
                
                print(f"   {script_path.name}: animate={has_animate}, "
                      f"params={has_params}")
                
            except Exception as e:
                print(f"   {script_path.name}: ❌ Error - {e}")
    
    return True


if __name__ == "__main__":
    main() 