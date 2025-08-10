#!/usr/bin/env python3
"""Standalone script to start the web server with working animations."""

from pathlib import Path
import sys
import threading

from core.conductor import Conductor
from core.config import ConfigManager
from web.app_simple import create_app, run_server

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))


def main():
    """Start the web server with proper initialization."""
    print("🚀 Starting LightBox Web Server")
    print("=" * 50)

    # Initialize configuration
    try:
        config = ConfigManager("config/settings.json")
        print(f"✅ Configuration loaded - Platform: {config.platform}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

    # Initialize conductor
    try:
        conductor = Conductor(config)
        print("✅ Conductor created")

        # Initialize hardware and animations
        if conductor.initialize():
            print("✅ System initialized successfully")
            print(f"   🎬 Animations loaded: {len(conductor.animations)}")
            if conductor.animations:
                print(f"   📱 Available: {list(conductor.animations.keys())}")
        else:
            print("⚠️  System initialization had issues, continuing with "
                  "web server...")
    except Exception as e:
        print(f"❌ Conductor initialization failed: {e}")
        return False

    # Start animation loop in background
    def run_animation_loop():
        """Run the animation loop in a separate thread."""
        try:
            conductor.run()
        except Exception as e:
            print(f"Animation loop error: {e}")

    # Start animation thread
    animation_thread = threading.Thread(target=run_animation_loop,
                                       daemon=True)
    animation_thread.start()
    print("✅ Animation loop started in background")

    # Create and run web application
    try:
        app = create_app(conductor)
        if app:
            print("✅ Web application created")
            print("\n🌐 Starting web server...")
            print("   📱 Main interface: http://lightbox.local:8888")
            print("   🎛️  Comprehensive controls: "
                  "http://lightbox.local:8888/comprehensive")
            print("   🔧 API status: http://lightbox.local:8888/api/status")
            print()

            # Start server
            run_server(app, host='0.0.0.0', port=8888, production=False)
        else:
            print("❌ Failed to create web application")
            return False
    except Exception as e:
        print(f"❌ Web server error: {e}")
        return False

    return True


if __name__ == "__main__":
    try:
        if main():
            print("✅ Server started successfully")
        else:
            print("❌ Server failed to start")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
