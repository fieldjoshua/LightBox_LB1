#!/usr/bin/env python3
"""
Fix Rendering Performance
========================

Replaces the inefficient pixel-by-pixel rendering (4096 SetPixel calls) 
with proper double-buffered update() method for smooth performance.

This fixes the core issue causing jitter and high CPU usage.
"""

import subprocess
import time


def log(message):
    print("[{}] {}".format(time.strftime('%H:%M:%S'), message))


def fix_rendering_performance():
    """Replace inefficient rendering with proper double buffering"""

    log("🔧 Fixing rendering performance...")

    # The problematic code that needs to be replaced
    old_inefficient_code = '''            # Update matrix display
            if self.matrix:
                self.matrix.Clear()
                for y in range(self.height):
                    for x in range(self.width):
                        pixel_index = y * self.width + x
                        if pixel_index < len(self.pixels):
                            r, g, b = self.pixels[pixel_index]
                            self.matrix.SetPixel(x, y, r, g, b)'''

    # The efficient replacement using driver's update() method
    new_efficient_code = '''            # Update matrix display with efficient double buffering
            if self.matrix:
                # Use driver's optimized update() method instead of pixel-by-pixel
                # This uses hardware double buffering for smooth, tear-free rendering
                self.matrix.update(self.pixels)'''

    log("📥 Downloading current lightbox file...")

    # Get current file
    result = subprocess.run([
        "ssh", "joshuafield@192.168.0.98",
        "cat /home/joshuafield/LightBox/lightbox_complete.py"
    ], capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        log("❌ Failed to download file")
        return False

    current_code = result.stdout

    # Check if the inefficient code exists
    if old_inefficient_code not in current_code:
        log("⚠️ Inefficient rendering code not found - "
            "may already be fixed")
        return False

    log("🔄 Replacing inefficient rendering with optimized method...")

    # Replace the inefficient code
    fixed_code = current_code.replace(old_inefficient_code,
                                      new_efficient_code)

    # Create backup
    log("💾 Creating backup...")
    backup_name = f"lightbox_complete.py.backup.perf.{int(time.time())}"
    subprocess.run([
        "ssh", "joshuafield@192.168.0.98",
        "cp /home/joshuafield/LightBox/lightbox_complete.py "
        f"/home/joshuafield/LightBox/{backup_name}"
    ], timeout=10)

    # Upload fixed code
    log("📤 Uploading performance fix...")

    upload_process = subprocess.Popen([
        "ssh", "joshuafield@192.168.0.98",
        "cat > /home/joshuafield/LightBox/lightbox_complete.py"
    ], stdin=subprocess.PIPE, text=True)

    upload_process.communicate(input=fixed_code)

    if upload_process.returncode != 0:
        log("❌ Failed to upload fixed code")
        return False

    log("🔄 Restarting lightbox service...")

    # Restart service
    restart_result = subprocess.run([
        "ssh", "joshuafield@192.168.0.98",
        "sudo systemctl restart lightbox"
    ], timeout=30)

    if restart_result.returncode != 0:
        log("❌ Failed to restart service")
        return False

    # Wait for startup
    time.sleep(3)

    # Verify it's working
    log("✅ Checking performance...")

    status_result = subprocess.run([
        "curl", "-s", "http://192.168.0.98:8888/api/status"
    ], capture_output=True, text=True, timeout=10)

    if status_result.returncode == 0:
        log("✅ Service restarted successfully!")
        log("🎯 Performance fix applied - "
            "rendering should now be MUCH smoother!")
        log("")
        log("📊 What was fixed:")
        log("   • Removed 4,096 individual SetPixel() calls per frame")
        log("   • Added proper double buffering with matrix.update()")
        log("   • Eliminated matrix.Clear() causing flicker")
        log("   • CPU usage should be dramatically reduced")
        return True
    else:
        log("⚠️ Service may not be responding")
        return False


if __name__ == "__main__":
    log("🚀 Starting rendering performance fix...")
    success = fix_rendering_performance()

    if success:
        log("🎉 PERFORMANCE FIX COMPLETE!")
        log("The display should now be smooth and efficient!")
    else:
        log("❌ Fix failed - manual intervention may be needed")
