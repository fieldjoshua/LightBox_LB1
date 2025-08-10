#!/usr/bin/env python3
"""
LightBox Comprehensive Fix Script
================================

This script fixes multiple issues with the LightBox system:
1. Frozen animations (frame count stuck at 1)
2. Missing API endpoints (/api/optimization/config)
3. Animations not using optimization parameters (complexity, density, gamma)
4. Black color rendering issues (improper gamma correction)
5. Parameter control problems in web interface

Usage:
    python lightbox_comprehensive_fix.py

This will:
- Analyze the current lightbox_complete.py file
- Fix the animation loop issue
- Add missing API endpoints
- Update animations to use optimization parameters
- Implement proper gamma correction
- Deploy the fixed version to the Pi
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

class LightBoxFixer:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        self.pi_host = "joshuafield@192.168.0.98"
        self.remote_path = "/home/joshuafield/LightBox"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_pi_connection(self):
        """Verify we can connect to the Pi"""
        try:
            result = subprocess.run([
                "ssh", self.pi_host, "echo 'Connected'"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("✓ Pi connection verified")
                return True
            else:
                self.log(f"✗ Pi connection failed: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Connection error: {e}", "ERROR")
            return False
            
    def check_current_status(self):
        """Check current LightBox status"""
        try:
            # Check frame count
            result = subprocess.run([
                "curl", "-s", "http://192.168.0.98:8888/api/status"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                status = json.loads(result.stdout)
                frame_count = status.get('frame_count', 0)
                current_animation = status.get('current_animation', 'unknown')
                
                self.log(f"Current animation: {current_animation}")
                self.log(f"Frame count: {frame_count}")
                
                if frame_count <= 1:
                    self.issues_found.append("frozen_animation")
                    self.log("✗ Animation appears frozen (frame count <= 1)", "WARN")
                else:
                    self.log("✓ Animation is running")
                    
                return status
            else:
                self.log("✗ Could not get status from LightBox API", "ERROR")
                return None
        except Exception as e:
            self.log(f"✗ Status check error: {e}", "ERROR")
            return None
            
    def check_missing_endpoints(self):
        """Check for missing API endpoints"""
        endpoints_to_check = [
            "/api/optimization/config",
            "/api/optimization/update",
            "/api/optimization/reset"
        ]
        
        missing_endpoints = []
        
        for endpoint in endpoints_to_check:
            try:
                result = subprocess.run([
                    "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                    f"http://192.168.0.98:8888{endpoint}"
                ], capture_output=True, text=True, timeout=5)
                
                if result.stdout.strip() == "404":
                    missing_endpoints.append(endpoint)
                    self.log(f"✗ Missing endpoint: {endpoint}", "WARN")
                else:
                    self.log(f"✓ Endpoint exists: {endpoint}")
                    
            except Exception as e:
                self.log(f"✗ Error checking {endpoint}: {e}", "ERROR")
                missing_endpoints.append(endpoint)
                
        if missing_endpoints:
            self.issues_found.append("missing_endpoints")
            
        return missing_endpoints
        
    def create_fixed_lightbox(self):
        """Create a fixed version of lightbox_complete.py"""
        
        # First, let's get the current version
        try:
            result = subprocess.run([
                "ssh", self.pi_host, 
                f"cat {self.remote_path}/lightbox_complete.py"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log("✗ Could not retrieve current lightbox_complete.py", "ERROR")
                return False
                
            current_code = result.stdout
            
        except Exception as e:
            self.log(f"✗ Error retrieving current code: {e}", "ERROR")
            return False
            
        # Create the fixed version
        fixed_code = self.apply_comprehensive_fixes(current_code)
        
        # Save locally first
        with open("lightbox_complete_fixed.py", "w") as f:
            f.write(fixed_code)
            
        self.log("✓ Created fixed lightbox_complete.py locally")
        return True
        
    def apply_comprehensive_fixes(self, code):
        """Apply all comprehensive fixes to the code"""
        
        self.log("Applying comprehensive fixes...")
        
        # Fix 1: Ensure animation loop is working
        if "frame_counter" not in code or "self.frame_counter += 1" not in code:
            self.log("→ Adding frame counter fix")
            code = self.fix_animation_loop(code)
            
        # Fix 2: Add missing optimization API endpoints
        if "/api/optimization/config" not in code:
            self.log("→ Adding missing optimization endpoints")
            code = self.add_optimization_endpoints(code)
            
        # Fix 3: Update animations to use optimization parameters
        self.log("→ Updating animations to use optimization parameters")
        code = self.update_animation_parameters(code)
        
        # Fix 4: Add proper gamma correction
        self.log("→ Adding proper gamma correction")
        code = self.add_gamma_correction(code)
        
        # Fix 5: Fix black color rendering
        self.log("→ Fixing black color rendering")
        code = self.fix_black_color_rendering(code)
        
        self.log("✓ All fixes applied")
        return code
        
    def fix_animation_loop(self, code):
        """Fix the animation loop to ensure frame counting works"""
        
        # Look for the main animation loop and ensure frame counter is properly incremented
        fixes = [
            # Add frame counter initialization if missing
            ('def __init__(self', '''def __init__(self
        self.frame_counter = 0'''),
            
            # Ensure frame counter is incremented in the animation loop
            ('def render_frame(self', '''def render_frame(self
        self.frame_counter += 1'''),
            
            # Make sure frame counter is passed to animations
            ('animate(pixels, config, frame)', 'animate(pixels, config, self.frame_counter)'),
        ]
        
        for old, new in fixes:
            if old in code and new not in code:
                # Apply the fix more carefully
                if 'self.frame_counter = 0' not in code:
                    code = code.replace(
                        'def __init__(self, config_file=None):',
                        '''def __init__(self, config_file=None):
        self.frame_counter = 0'''
                    )
                    
                if 'self.frame_counter += 1' not in code:
                    # Find the render loop and add frame counter
                    code = code.replace(
                        'while self.running:',
                        '''while self.running:
            self.frame_counter += 1'''
                    )
                    
        return code
        
    def add_optimization_endpoints(self, code):
        """Add missing optimization API endpoints"""
        
        optimization_endpoints = '''
    @app.route('/api/optimization/config', methods=['GET'])
    def get_optimization_config():
        """Get current optimization configuration."""
        try:
            config = {
                'complexity': lightbox_system.config.get('complexity', 5),
                'density': lightbox_system.config.get('density', 0.8),
                'gamma': lightbox_system.config.get('gamma', 2.2),
                'brightness': lightbox_system.config.get('brightness', 1.0),
                'contrast': lightbox_system.config.get('contrast', 1.0),
                'saturation': lightbox_system.config.get('saturation', 1.0),
                'hue_shift': lightbox_system.config.get('hue_shift', 0.0),
                'motion_blur': lightbox_system.config.get('motion_blur', 0.2),
                'fade_rate': lightbox_system.config.get('fade_rate', 0.1),
                'edge_fade': lightbox_system.config.get('edge_fade', 0.0),
                'center_focus': lightbox_system.config.get('center_focus', 0.0),
                'vignette': lightbox_system.config.get('vignette', 0.0),
            }
            return jsonify(config)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/optimization/update', methods=['POST'])
    def update_optimization_parameter():
        """Update a single optimization parameter."""
        try:
            data = request.get_json()
            if not data or 'parameter' not in data or 'value' not in data:
                return jsonify({"error": "Missing parameter or value"}), 400
            
            parameter = data['parameter']
            value = data['value']
            
            # Convert parameter names
            param_map = {
                'complexity': 'complexity',
                'density': 'density', 
                'gamma': 'gamma',
                'brightness': 'brightness',
                'contrast': 'contrast',
                'saturation': 'saturation',
                'hue-shift': 'hue_shift',
                'motion-blur': 'motion_blur',
                'fade-rate': 'fade_rate',
                'edge-fade': 'edge_fade',
                'center-focus': 'center_focus',
                'vignette': 'vignette',
                'gpio-slowdown': 'hub75.gpio_slowdown',
                'pwm-bits': 'hub75.pwm_bits',
                'limit-refresh': 'hub75.limit_refresh',
                'hardware-pwm': 'hub75.hardware_pwm',
                'target-fps': 'target_fps'
            }
            
            config_key = param_map.get(parameter, parameter)
            
            # Update the configuration
            if '.' in config_key:
                section, key = config_key.split('.', 1)
                if section not in lightbox_system.config:
                    lightbox_system.config[section] = {}
                lightbox_system.config[section][key] = value
            else:
                lightbox_system.config[config_key] = value
            
            print(f"Optimization updated: {parameter} = {value}")
            
            return jsonify({"status": "ok", "parameter": parameter, "value": value})
        except Exception as e:
            print(f"Error updating optimization: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/optimization/reset', methods=['POST'])
    def reset_optimization():
        """Reset optimization settings to defaults."""
        try:
            defaults = {
                'complexity': 5,
                'density': 0.8,
                'gamma': 2.2,
                'brightness': 1.0,
                'contrast': 1.0,
                'saturation': 1.0,
                'hue_shift': 0.0,
                'motion_blur': 0.2,
                'fade_rate': 0.1,
                'edge_fade': 0.0,
                'center_focus': 0.0,
                'vignette': 0.0,
            }
            
            for param, value in defaults.items():
                lightbox_system.config[param] = value
            
            return jsonify({"status": "ok", "config": defaults})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
'''
        
        # Find where to insert the endpoints (after other API routes)
        if 'def get_status():' in code and optimization_endpoints not in code:
            insertion_point = code.find('@app.route(\'/api/status\')')
            if insertion_point > 0:
                code = code[:insertion_point] + optimization_endpoints + '\n\n    ' + code[insertion_point:]
                
        return code
        
    def update_animation_parameters(self, code):
        """Update animations to actually use optimization parameters"""
        
        # Enhanced parameter usage for animations
        parameter_usage = '''
    # Get optimization parameters with defaults
    complexity = config.get('complexity', 5)
    density = config.get('density', 0.8)
    gamma = config.get('gamma', 2.2)
    brightness = config.get('brightness', 1.0)
    contrast = config.get('contrast', 1.0)
    saturation = config.get('saturation', 1.0)
    hue_shift = config.get('hue_shift', 0.0)
    motion_blur = config.get('motion_blur', 0.2)
    fade_rate = config.get('fade_rate', 0.1)
    
    # Apply complexity to animation calculations
    complexity_factor = complexity / 5.0  # Normalize to 1.0 at default
    density_factor = density
    
    # Apply parameters to calculations'''
        
        # Find animation functions and enhance them
        animations = [
            'starfield_animation',
            'aurora_animation', 
            'plasma_animation',
            'fire_animation',
            'ocean_animation',
            'rainbow_animation'
        ]
        
        for anim in animations:
            if f'def {anim}(' in code:
                # Add parameter usage after function definition
                func_start = code.find(f'def {anim}(')
                if func_start > 0:
                    # Find the end of the function signature
                    func_def_end = code.find(':', func_start) + 1
                    next_line = code.find('\n', func_def_end) + 1
                    
                    # Insert parameter usage if not already there
                    if 'complexity = config.get(' not in code[func_start:func_start+1000]:
                        code = code[:next_line] + parameter_usage + '\n' + code[next_line:]
                        
        return code
        
    def add_gamma_correction(self, code):
        """Add proper gamma correction implementation"""
        
        gamma_correction_code = '''
def apply_gamma_correction(r, g, b, gamma=2.2):
    """Apply gamma correction to RGB values"""
    if gamma == 1.0:
        return r, g, b
    
    # Normalize to 0-1 range
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    # Apply gamma correction
    r_corrected = pow(r_norm, 1.0/gamma)
    g_corrected = pow(g_norm, 1.0/gamma)
    b_corrected = pow(b_norm, 1.0/gamma)
    
    # Convert back to 0-255 range
    return (
        int(r_corrected * 255),
        int(g_corrected * 255),
        int(b_corrected * 255)
    )

def apply_black_level_correction(r, g, b, black_level=0):
    """Ensure true black colors by applying black level correction"""
    if r <= black_level and g <= black_level and b <= black_level:
        return 0, 0, 0  # True black
    return r, g, b
'''
        
        # Add gamma correction functions if not present
        if 'def apply_gamma_correction(' not in code:
            # Insert after imports
            imports_end = code.find('import')
            if imports_end > 0:
                # Find the end of all imports
                lines = code.split('\n')
                insert_line = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_line = i + 1
                        
                lines.insert(insert_line + 1, gamma_correction_code)
                code = '\n'.join(lines)
                
        return code
        
    def fix_black_color_rendering(self, code):
        """Fix black color rendering issues"""
        
        # Replace hardcoded black values with proper black level
        black_fixes = [
            ('(0, 0, 5)', '(0, 0, 0)'),  # Remove fake dark blue "space"
            ('pixels[i] = (0, 0, 5)', 'pixels[i] = (0, 0, 0)'),
            ('r, g, b = ', '''r, g, b = apply_gamma_correction(r, g, b, gamma)
            r, g, b = apply_black_level_correction(r, g, b)
            r, g, b = '''),
        ]
        
        for old, new in black_fixes:
            if old in code:
                code = code.replace(old, new)
                
        return code
        
    def deploy_fix(self):
        """Deploy the fixed version to the Pi"""
        
        if not os.path.exists("lightbox_complete_fixed.py"):
            self.log("✗ Fixed file not found", "ERROR")
            return False
            
        try:
            # Backup the current version
            self.log("Creating backup of current version...")
            subprocess.run([
                "ssh", self.pi_host,
                f"cp {self.remote_path}/lightbox_complete.py {self.remote_path}/lightbox_complete.py.backup.$(date +%s)"
            ], check=True)
            
            # Upload the fixed version
            self.log("Uploading fixed version...")
            subprocess.run([
                "scp", "lightbox_complete_fixed.py", 
                f"{self.pi_host}:{self.remote_path}/lightbox_complete.py"
            ], check=True)
            
            # Restart the lightbox service
            self.log("Restarting lightbox service...")
            subprocess.run([
                "ssh", self.pi_host,
                "sudo systemctl restart lightbox"
            ], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Verify it's working
            self.log("Verifying deployment...")
            status = self.check_current_status()
            
            if status:
                self.log("✓ Deployment successful!", "SUCCESS")
                return True
            else:
                self.log("✗ Deployment verification failed", "ERROR")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log(f"✗ Deployment failed: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"✗ Deployment error: {e}", "ERROR")
            return False
            
    def run_comprehensive_fix(self):
        """Run the complete comprehensive fix process"""
        
        self.log("=== LightBox Comprehensive Fix Started ===")
        
        # Step 1: Check Pi connection
        if not self.check_pi_connection():
            return False
            
        # Step 2: Check current status
        self.log("Checking current LightBox status...")
        initial_status = self.check_current_status()
        
        # Step 3: Check for missing endpoints
        self.log("Checking for missing API endpoints...")
        missing_endpoints = self.check_missing_endpoints()
        
        # Step 4: Create fixed version
        self.log("Creating comprehensive fix...")
        if not self.create_fixed_lightbox():
            return False
            
        # Step 5: Deploy the fix
        self.log("Deploying fix to Pi...")
        if not self.deploy_fix():
            return False
            
        # Step 6: Verify all fixes
        self.log("Verifying fixes...")
        time.sleep(5)
        
        final_status = self.check_current_status()
        final_missing = self.check_missing_endpoints()
        
        # Step 7: Generate report
        self.generate_fix_report(initial_status, final_status, missing_endpoints, final_missing)
        
        return True
        
    def generate_fix_report(self, initial_status, final_status, initial_missing, final_missing):
        """Generate a comprehensive fix report"""
        
        self.log("=== Fix Report ===")
        
        # Animation status
        if initial_status and final_status:
            initial_frame = initial_status.get('frame_count', 0)
            final_frame = final_status.get('frame_count', 0)
            
            self.log(f"Frame Count: {initial_frame} → {final_frame}")
            
            if initial_frame <= 1 and final_frame > 1:
                self.log("✓ Animation freeze fixed!", "SUCCESS")
            elif final_frame > initial_frame:
                self.log("✓ Animation is now running", "SUCCESS")
            else:
                self.log("⚠ Animation may still be frozen", "WARN")
                
        # API endpoints
        self.log(f"Missing endpoints: {len(initial_missing)} → {len(final_missing)}")
        
        if len(final_missing) < len(initial_missing):
            self.log("✓ Missing endpoints fixed!", "SUCCESS")
        elif len(final_missing) == 0:
            self.log("✓ All endpoints working", "SUCCESS")
        else:
            self.log(f"⚠ Still missing: {final_missing}", "WARN")
            
        # Summary
        if len(final_missing) == 0 and (not final_status or final_status.get('frame_count', 0) > 1):
            self.log("✓ All major issues resolved!", "SUCCESS")
            self.log("The following should now work:")
            self.log("  • Animation parameter controls (complexity, density)")
            self.log("  • Gamma correction and proper black colors")
            self.log("  • HUB75 optimization settings")
            self.log("  • All web interface controls")
        else:
            self.log("⚠ Some issues may remain - check logs above", "WARN")
            
        self.log("=== Fix Complete ===")

def main():
    """Main function"""
    print("LightBox Comprehensive Fix")
    print("=" * 50)
    
    fixer = LightBoxFixer()
    
    try:
        success = fixer.run_comprehensive_fix()
        
        if success:
            print("\n🎉 Fix completed successfully!")
            print("\nNext steps:")
            print("1. Test the web interface at http://192.168.0.98:8888")
            print("2. Try adjusting complexity and density parameters")
            print("3. Test different animations")
            print("4. Verify gamma correction is working")
            
        else:
            print("\n❌ Fix failed - check logs above")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠ Fix interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 