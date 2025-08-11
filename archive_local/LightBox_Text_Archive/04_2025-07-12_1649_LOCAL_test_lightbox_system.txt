#!/usr/bin/env python3
"""
LightBox System Test - Comprehensive Verification
Tests all system components and animations
"""

import sys
import time
import json
from pathlib import Path

def test_imports():
    """Test that all core components can be imported"""
    print("🔍 Testing imports...")
    try:
        from core.conductor import Conductor
        from core.config import ConfigManager
        from web.app_simple import create_app
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("🔍 Testing configuration...")
    try:
        from core.config import ConfigManager
        config = ConfigManager("config/settings.json")
        print(f"✅ Config loaded - Platform: {config.platform}")
        print(f"✅ HUB75 Config: {config.get('hub75.rows')}x{config.get('hub75.cols')}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_conductor():
    """Test conductor initialization and animation loading"""
    print("🔍 Testing conductor and animations...")
    try:
        from core.conductor import Conductor
        conductor = Conductor()
        result = conductor.initialize()
        
        if result:
            print(f"✅ Conductor initialized successfully")
            print(f"✅ Animations loaded: {len(conductor.animations)}")
            
            # List first 10 animations
            anims = list(conductor.animations.keys())[:10]
            print(f"✅ Sample animations: {', '.join(anims)}")
            return True
        else:
            print("❌ Conductor initialization failed")
            return False
    except Exception as e:
        print(f"❌ Conductor error: {e}")
        return False

def test_web_app():
    """Test web application creation"""
    print("🔍 Testing web application...")
    try:
        from core.conductor import Conductor
        from web.app_simple import create_app
        
        conductor = Conductor()
        conductor.initialize()
        app = create_app(conductor)
        
        if app:
            print("✅ Web application created successfully")
            return True
        else:
            print("❌ Web application creation failed")
            return False
    except Exception as e:
        print(f"❌ Web app error: {e}")
        return False

def test_animation_syntax():
    """Test that animations can be imported without syntax errors"""
    print("🔍 Testing animation scripts...")
    scripts_dir = Path("scripts")
    
    if not scripts_dir.exists():
        print("❌ Scripts directory not found")
        return False
    
    passed = 0
    failed = 0
    
    for script_file in scripts_dir.glob("*.py"):
        if script_file.name.startswith("__"):
            continue
            
        try:
            # Test if the file can be compiled
            with open(script_file, 'r') as f:
                content = f.read()
            compile(content, str(script_file), 'exec')
            passed += 1
        except SyntaxError as e:
            print(f"❌ Syntax error in {script_file.name}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  Other error in {script_file.name}: {e}")
    
    print(f"✅ Animation syntax test: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Run all tests"""
    print("🚀 LightBox System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Conductor & Animations", test_conductor),
        ("Web Application", test_web_app),
        ("Animation Syntax", test_animation_syntax)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System ready for deployment!")
        print("🚀 You can now start the full system with: sudo python3 main.py")
    else:
        print("⚠️  Some tests failed - please review errors above")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 