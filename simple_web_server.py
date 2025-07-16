#!/usr/bin/env python3
"""Simple web server to demonstrate the working HUB75 system."""

import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template

from core.config import ConfigManager
from core.conductor import Conductor

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

app = Flask(__name__)


# Global conductor instance
conductor = None


@app.route('/')
def index():
    """Serve the main interface."""
    return render_template('index.html')


@app.route('/comprehensive')
def comprehensive():
    """Serve the comprehensive parameter interface."""
    return render_template('comprehensive.html')


@app.route('/api/status')
def get_status():
    """Get current system status."""
    if conductor:
        return jsonify({
            "status": "running",
            "platform": conductor.config.platform,
            "matrix_type": conductor.config.get("matrix_type"),
            "animations_loaded": len(conductor.animations),
            "available_animations": list(conductor.animations.keys()),
            "current_animation": (conductor.current_animation.name 
                                 if conductor.current_animation else None),
            "matrix_size": (f"{conductor.config.get('hub75.cols', 64)}x"
                           f"{conductor.config.get('hub75.rows', 64)}")
        })
    else:
        return jsonify({"status": "initializing"})


@app.route('/api/animations')
def get_animations():
    """Get available animations."""
    if conductor:
        return jsonify({
            "animations": list(conductor.animations.keys()),
            "current": (conductor.current_animation.name 
                       if conductor.current_animation else None)
        })
    else:
        return jsonify({"animations": [], "current": None})


@app.route('/api/animations/<name>', methods=['POST'])
def set_animation(name):
    """Set current animation."""
    if conductor and name in conductor.animations:
        success = conductor.set_animation(name)
        return jsonify({"success": success, "animation": name})
    else:
        return jsonify({"success": False, "error": "Animation not found"})


def main():
    """Start the web server."""
    global conductor
    
    print("🚀 Starting Simple LightBox Web Server")
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
                current_name = (conductor.current_animation.name 
                               if conductor.current_animation else 'None')
                print(f"   🎯 Current: {current_name}")
        else:
            print("⚠️  System initialization had issues, continuing...")
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
    
    # Start web server
    try:
        print("✅ Web application created")
        print("\n🌐 Starting web server...")
        print("   📱 Main interface: http://lightbox.local:8888")
        print("   🎛️  Comprehensive controls: "
              "http://lightbox.local:8888/comprehensive")
        print("   🔧 API status: http://lightbox.local:8888/api/status")
        print("   🎬 Animations API: http://lightbox.local:8888/api/animations")
        print()
        
        # Use simple Flask run method
        app.run(host='0.0.0.0', port=8888, debug=False, use_reloader=False)
        
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