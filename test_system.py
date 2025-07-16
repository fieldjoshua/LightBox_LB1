#!/usr/bin/env python3
"""
Test script to verify LightBox Organized system components
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all core modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Test core modules
        from core.conductor import Conductor
        from core.config import ConfigManager
        from core.performance import PerformanceMonitor
        print("✅ Core modules imported successfully")
        
        # Test driver modules
        from drivers.matrix_driver import MatrixDriver
        from drivers.hub75_driver import HUB75Driver
        print("✅ Driver modules imported successfully")
        
        # Test hardware modules
        from hardware.hardware_manager import HardwareManager
        print("✅ Hardware modules imported successfully")
        
        # Test utility modules
        from utils.color_utils import hsv_to_rgb, rgb_to_hsv
        from utils.frame_utils import FrameBuffer, create_frame
        print("✅ Utility modules imported successfully")
        
        # Test web modules
        from api.WebAPI import create_app
        print("✅ Web modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from core.config import ConfigManager
        
        # Test loading configuration
        config = ConfigManager("config/settings.json")
        
        # Test some key settings
        matrix_type = config.get("matrix_type")
        brightness = config.get("brightness")
        
        print(f"✅ Configuration loaded: matrix_type={matrix_type}, brightness={brightness}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "core",
        "drivers", 
        "hardware",
        "web",
        "utils",
        "scripts",
        "config",
        "animations",
        "tests",
        "documentation"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    else:
        print("✅ All required directories exist")
        return True


def test_files():
    """Test that key files exist."""
    print("\nTesting key files...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "install_rgb_matrix.sh",
        "config/settings.json",
        "README.md"
    ]
    
    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("LightBox Organized - System Test")
    print("=" * 50)
    
    tests = [
        test_directory_structure,
        test_files,
        test_imports,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! LightBox Organized is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip3 install -r requirements.txt")
        print("2. Install HUB75 library: sudo bash install_rgb_matrix.sh")
        print("3. Start LightBox: sudo python3 main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 50)


if __name__ == "__main__":
    main() 