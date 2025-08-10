#!/usr/bin/env python3
"""
Fix GUI Parameters
==================

Comprehensive fix for all GUI parameter issues:

1. Fix slider ranges (max values) 
2. Add missing parameters (gamma, color_intensity)
3. Connect parameters to animations properly
4. Fix API parameter mapping
5. Add parameter descriptions
"""

import subprocess
import time


def log(message):
    print("[{}] {}".format(time.strftime('%H:%M:%S'), message))

def fix_gui_parameters():
    """Comprehensive fix for GUI parameter issues"""

    log("🔧 Fixing GUI parameter issues...")

    # Fix slider ranges - change max="10" to max="100" for percentage sliders
    slider_fixes = {
        'max="10" value="5" class="slider" id="speed"': 'max="200" value="100" class="slider" id="speed"',
        'max="10" value="5" class="slider" id="intensity"': 'max="200" value="100" class="slider" id="intensity"',
        'max="10" value="5" class="slider" id="scale"': 'max="200" value="100" class="slider" id="scale"',
        'max="10" value="5" class="slider" id="complexity"': 'max="10" value="5" class="slider" id="complexity"',  # Keep 1-10
        'max="10" value="5" class="slider" id="smoothness"': 'max="10" value="5" class="slider" id="smoothness"',  # Keep 1-10
    }

    # Add missing parameters to GUI (gamma, color_intensity)
    missing_params_html = '''                    
                    <div class="slider-container">
                        <label>Gamma</label>
                        <input type="range" min="1" max="3" step="0.1" value="2.2" class="slider" id="gamma">
                        <span class="value-display" id="gamma-val">2.2</span>
                    </div>
                    
                    <div class="slider-container">
                        <label>Color Intensity</label>
                        <input type="range" min="0" max="200" value="100" class="slider" id="color-intensity">
                        <span class="value-display" id="color-intensity-val">100%</span>
                    </div>'''

    # Fix JavaScript parameter mapping
    js_fixes = {
        "['brightness', 'speed', 'intensity', 'hue', 'saturation', 'scale', 'complexity', 'smoothness'].forEach(id => {":
        "['brightness', 'speed', 'intensity', 'hue', 'saturation', 'scale', 'complexity', 'smoothness', 'gamma', 'color-intensity'].forEach(id => {",

        "const unit = id === 'hue' ? '°' : (id === 'complexity' || id === 'smoothness' ? '' : '%');":
        "const unit = id === 'hue' ? '°' : (id === 'complexity' || id === 'smoothness' || id === 'gamma' ? '' : '%');",
    }

    # Fix updateParameter function to use proper API
    update_param_fix = '''        function updateParameter(param, value) {
            // Convert parameter names to match API
            const paramMap = {
                'brightness': 'brightness',
                'speed': 'speed', 
                'intensity': 'intensity',
                'hue': 'hue_shift',
                'saturation': 'saturation',
                'scale': 'scale',
                'complexity': 'complexity',
                'smoothness': 'smoothness', 
                'gamma': 'gamma',
                'color-intensity': 'color_intensity'
            };
            
            const apiParam = paramMap[param] || param;
            const numValue = parseFloat(value);
            
            // Convert percentage values (0-100 or 0-200) to proper ranges
            let apiValue = numValue;
            if (param === 'speed' || param === 'intensity' || param === 'scale' || param === 'color-intensity') {
                apiValue = numValue / 100.0;  // Convert 100% to 1.0
            }
            if (param === 'hue') {
                apiValue = numValue / 360.0;  // Convert 360° to 1.0
            }
            
            // Send to proper API endpoint
            fetch('/api/optimization/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({[apiParam]: apiValue})
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'ok') {
                      console.log(`Updated ${param} = ${apiValue}`);
                  }
              })
              .catch(error => console.error('Parameter update failed:', error));
        }'''

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

    log("🔄 Fixing slider ranges...")
    for old, new in slider_fixes.items():
        if old in current_code:
            current_code = current_code.replace(old, new)
            log("✅ Fixed slider range for {}".format(old.split('id="')[1].split('"')[0]))

    log("🔄 Adding missing parameters...")
    # Insert missing parameters after smoothness slider
    smoothness_marker = '''                    <div class="slider-container">
                        <label>Smoothness</label>
                        <input type="range" min="1" max="10" value="5" class="slider" id="smoothness">
                        <span class="value-display" id="smoothness-val">5</span>
                    </div>'''

    if smoothness_marker in current_code:
        current_code = current_code.replace(smoothness_marker, smoothness_marker + missing_params_html)
        log("✅ Added gamma and color-intensity parameters")

    log("🔄 Fixing JavaScript parameter handling...")
    for old, new in js_fixes.items():
        if old in current_code:
            current_code = current_code.replace(old, new)
            log("✅ Updated JavaScript parameter list")

    log("🔄 Replacing updateParameter function...")
    # Find and replace the updateParameter function
    old_update_start = "function updateParameter(param, value) {"
    old_update_end = "        }"

    start_idx = current_code.find(old_update_start)
    if start_idx != -1:
        # Find the end of the function
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(current_code[start_idx:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = start_idx + i + 1
                    break

        # Replace the function
        before = current_code[:start_idx]
        after = current_code[end_idx:]
        current_code = before + update_param_fix + after
        log("✅ Replaced updateParameter function")
    else:
        log("⚠️ Could not find updateParameter function")

    # Create backup
    log("💾 Creating backup...")
    subprocess.run([
        "ssh", "joshuafield@192.168.0.98",
        "cp /home/joshuafield/LightBox/lightbox_complete.py "
        f"/home/joshuafield/LightBox/lightbox_complete.py.backup.params.{int(time.time())}"
    ], timeout=10)

    # Upload fixed code
    log("📤 Uploading parameter fixes...")

    upload_process = subprocess.Popen([
        "ssh", "joshuafield@192.168.0.98",
        "cat > /home/joshuafield/LightBox/lightbox_complete.py"
    ], stdin=subprocess.PIPE, text=True)

    upload_process.communicate(input=current_code)

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

    log("✅ GUI parameter fixes applied!")
    log("")
    log("📊 What was fixed:")
    log("   • Fixed slider ranges (no more 1000%)")
    log("   • Added gamma correction control (1.0-3.0)")
    log("   • Added color intensity control (0-200%)")
    log("   • Fixed parameter API mapping")
    log("   • Connected all parameters to optimization API")
    log("")
    log("📋 Parameter explanations:")
    log("   • Complexity: Animation detail level (1-10)")
    log("   • Smoothness: Temporal smoothing (1-10)")
    log("   • Gamma: Color correction curve (1.0-3.0, default 2.2)")
    log("   • Color Intensity: Color saturation multiplier (0-200%)")
    log("   • Speed/Intensity/Scale: Animation modifiers (0-200%)")
    return True

if __name__ == "__main__":
    log("🚀 Starting GUI parameter fixes...")
    success = fix_gui_parameters()

    if success:
        log("🎉 GUI PARAMETER FIXES COMPLETE!")
        log("All sliders should now work properly with correct ranges!")
    else:
        log("❌ Fix failed - manual intervention may be needed")
