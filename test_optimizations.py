#!/usr/bin/env python3
"""
LightBox Optimization Test Script
================================

This script tests the applied optimizations and measures performance.
"""

import json
import sys
import time


def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")

    try:
        with open('config/settings_optimized.json') as f:
            config = json.load(f)

        print("✅ Configuration loaded successfully")
        print(f"   PWM bits: {config['hub75']['pwm_bits']}")
        print(f"   GPIO slowdown: {config['hub75']['gpio_slowdown']}")
        print(f"   Hardware PWM: {config['hub75']['hardware_pwm']}")
        print(f"   Refresh limit: {config['hub75']['limit_refresh']}")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_matrix_initialization():
    """Test matrix controller initialization"""
    print("\n🖥️  Testing Matrix Controller...")

    try:
        sys.path.insert(0, '.')
        from core.config import ConfigManager
        from core.optimized_matrix_controller import OptimizedMatrixController

        config = ConfigManager('config/settings_optimized.json')
        controller = OptimizedMatrixController(config)

        print("✅ Matrix controller initialized")

        # Test double buffering
        with controller.render_frame() as canvas:
            if canvas:
                print("✅ Double buffering working")
            else:
                print("⚠️  Running in simulation mode")

        print(f"   Dimensions: {controller.get_dimensions()}")

        controller.shutdown()
        return True

    except Exception as e:
        print(f"❌ Matrix test failed: {e}")
        return False

def test_system_optimizations():
    """Test system-level optimizations"""
    print("\n⚙️  Testing System Optimizations...")

    # Check CPU isolation
    try:
        with open('/proc/cmdline') as f:
            cmdline = f.read()

        if 'isolcpus=3' in cmdline:
            print("✅ CPU isolation configured")
        else:
            print("⚠️  CPU isolation not found")
    except:
        print("❌ Could not check CPU isolation")

    # Check audio blacklist
    blacklist_path = "/etc/modprobe.d/blacklist-rgb-matrix.conf"
    if os.path.exists(blacklist_path):
        print("✅ Audio modules blacklisted")
    else:
        print("⚠️  Audio blacklist not found")

    # Check boot config
    try:
        with open('/boot/config.txt') as f:
            config = f.read()

        if 'dtparam=audio=off' in config:
            print("✅ Audio disabled in boot config")
        else:
            print("⚠️  Audio not disabled")

        if 'gpu_mem=16' in config:
            print("✅ GPU memory optimized")
        else:
            print("⚠️  GPU memory not optimized")
    except:
        print("❌ Could not check boot config")

def run_performance_benchmark():
    """Run performance benchmark"""
    print("\n🚀 Running Performance Benchmark...")

    try:
        from core.config import ConfigManager
        from core.optimized_animation_loop import OptimizedAnimationLoop
        from core.optimized_matrix_controller import OptimizedMatrixController

        config = ConfigManager('config/settings_optimized.json')
        controller = OptimizedMatrixController(config)
        loop = OptimizedAnimationLoop(controller, target_fps=30)

        # Simple test animation
        def test_animation(pixels, params, frame):
            """Simple moving pattern"""
            width, height = controller.get_dimensions()
            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx < len(pixels):
                        brightness = (frame + x + y) % 64
                        pixels[idx] = (brightness, brightness//2, brightness//4)

        loop.set_animation(test_animation)
        loop.start()

        print("Running 5-second benchmark...")
        time.sleep(5)

        stats = loop.get_stats()
        loop.stop()
        controller.shutdown()

        print("📊 Performance Results:")
        print(f"   Target FPS: {stats.get('target_fps', 0):.1f}")
        print(f"   Actual FPS: {stats.get('actual_fps', 0):.1f}")
        print(f"   Frame time: {stats.get('frame_time_avg', 0):.2f}ms avg")
        print(f"   Frames rendered: {stats.get('frame_count', 0)}")

        if stats.get('actual_fps', 0) >= stats.get('target_fps', 30) * 0.9:
            print("✅ Performance test PASSED")
            return True
        else:
            print("⚠️  Performance below target")
            return False

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 LightBox Optimization Tests")
    print("=" * 40)

    tests = [
        ("Configuration", test_configuration),
        ("Matrix Controller", test_matrix_initialization),
        ("System Optimizations", test_system_optimizations),
        ("Performance Benchmark", run_performance_benchmark)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 40)
    print("📋 Test Summary:")

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All optimizations working correctly!")
        print("   Your LightBox should now have smooth, jitter-free animations.")
    else:
        print("\n⚠️  Some issues detected. Check the output above.")
        print("   You may need to reboot for some changes to take effect.")

if __name__ == "__main__":
    main()
