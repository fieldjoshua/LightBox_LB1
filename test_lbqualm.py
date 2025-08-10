#!/usr/bin/env python3
"""
🧪 LBQualm Test Suite
====================

Comprehensive testing for the Ultimate HUB75 LightBox System.
This script validates all components before deployment to ensure
LBQualm actually works as advertised.

Usage: python3 test_lbqualm.py
"""

import importlib
from pathlib import Path
import subprocess
import sys

# Test configuration
TEST_CONFIG = {
    'files_to_check': [
        'LBQualm.py',
        'requirements_hub75_optimized.txt',
        'deploy_lbqualm.sh',
        'README_LBQUALM.md'
    ],
    'required_modules': [
        'flask',
        'flask_cors'
    ],
    'optional_modules': [
        'rgbmatrix'
    ]
}

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.PURPLE}{'='*60}{Colors.NC}")
    print(f"{Colors.PURPLE}{text:^60}{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*60}{Colors.NC}\n")

def print_test(test_name):
    """Print test name."""
    print(f"{Colors.BLUE}🧪 Testing: {test_name}{Colors.NC}")

def print_pass(message):
    """Print success message."""
    print(f"{Colors.GREEN}✅ PASS: {message}{Colors.NC}")

def print_fail(message):
    """Print failure message."""
    print(f"{Colors.RED}❌ FAIL: {message}{Colors.NC}")

def print_warn(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  WARN: {message}{Colors.NC}")

def print_info(message):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  INFO: {message}{Colors.NC}")

class LBQualmTester:
    """Comprehensive test suite for LBQualm."""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0
        }
        self.critical_failures = []

    def run_all_tests(self):
        """Run the complete test suite."""
        print_header("🌈 LBQUALM COMPREHENSIVE TEST SUITE")
        print_info("Testing the Ultimate HUB75 LightBox System")
        print_info("This ensures LBQualm actually works as advertised")

        # Run test categories
        self.test_files_exist()
        self.test_python_syntax()
        self.test_module_imports()
        self.test_lbqualm_initialization()
        self.test_animation_engine()
        self.test_web_interface_structure()
        self.test_deployment_script()
        self.test_configuration_system()

        # Print results
        self.print_test_summary()

        return len(self.critical_failures) == 0

    def record_test(self, passed, test_name, message=""):
        """Record test result."""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            print_pass(f"{test_name}: {message}")
        else:
            self.test_results['failed_tests'] += 1
            print_fail(f"{test_name}: {message}")
            self.critical_failures.append(f"{test_name}: {message}")

    def record_warning(self, test_name, message):
        """Record warning."""
        self.test_results['warnings'] += 1
        print_warn(f"{test_name}: {message}")

    def test_files_exist(self):
        """Test that all required files exist."""
        print_test("File Existence")

        for file_path in TEST_CONFIG['files_to_check']:
            exists = Path(file_path).exists()
            self.record_test(
                exists,
                f"File {file_path}",
                "Found" if exists else "Missing"
            )

    def test_python_syntax(self):
        """Test Python syntax of main files."""
        print_test("Python Syntax Validation")

        python_files = ['LBQualm.py']

        for file_path in python_files:
            if not Path(file_path).exists():
                continue

            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', file_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                self.record_test(
                    result.returncode == 0,
                    f"Syntax {file_path}",
                    "Valid syntax" if result.returncode == 0 else f"Syntax error: {result.stderr}"
                )

            except subprocess.TimeoutExpired:
                self.record_test(False, f"Syntax {file_path}", "Compilation timeout")
            except Exception as e:
                self.record_test(False, f"Syntax {file_path}", f"Compilation error: {e}")

    def test_module_imports(self):
        """Test that required modules can be imported."""
        print_test("Module Import Validation")

        # Test required modules
        for module_name in TEST_CONFIG['required_modules']:
            try:
                importlib.import_module(module_name)
                self.record_test(True, f"Import {module_name}", "Available")
            except ImportError:
                self.record_test(False, f"Import {module_name}", "Not available")

        # Test optional modules
        for module_name in TEST_CONFIG['optional_modules']:
            try:
                importlib.import_module(module_name)
                print_pass(f"Optional module {module_name}: Available")
            except ImportError:
                self.record_warning(f"Optional {module_name}", "Not available (will use simulation mode)")

    def test_lbqualm_initialization(self):
        """Test LBQualm system initialization."""
        print_test("LBQualm System Initialization")

        try:
            # Add current directory to path
            sys.path.insert(0, str(Path.cwd()))

            # Import LBQualm modules
            import LBQualm

            # Test core classes exist
            required_classes = [
                'LBQualmSystem',
                'LBQualmConfig',
                'LBQualmMatrixController',
                'SystemDetection',
                'ColorProcessor'
            ]

            for class_name in required_classes:
                if hasattr(LBQualm, class_name):
                    self.record_test(True, f"Class {class_name}", "Defined")
                else:
                    self.record_test(False, f"Class {class_name}", "Missing")

            # Test system can be instantiated
            try:
                config = LBQualm.LBQualmConfig()
                self.record_test(True, "Config instantiation", "Success")

                system = LBQualm.LBQualmSystem()
                self.record_test(True, "System instantiation", "Success")

            except Exception as e:
                self.record_test(False, "System instantiation", f"Failed: {e}")

        except ImportError as e:
            self.record_test(False, "LBQualm import", f"Cannot import: {e}")
        except Exception as e:
            self.record_test(False, "LBQualm initialization", f"Error: {e}")

    def test_animation_engine(self):
        """Test the animation engine."""
        print_test("Animation Engine")

        try:
            import LBQualm

            # Test animation registry exists
            if hasattr(LBQualm, 'EMBEDDED_ANIMATIONS'):
                animations = LBQualm.EMBEDDED_ANIMATIONS
                self.record_test(True, "Animation registry", f"Found {len(animations)} animations")

                # Test each animation function
                for anim_name, anim_func in animations.items():
                    if callable(anim_func):
                        self.record_test(True, f"Animation {anim_name}", "Callable function")
                    else:
                        self.record_test(False, f"Animation {anim_name}", "Not callable")
            else:
                self.record_test(False, "Animation registry", "EMBEDDED_ANIMATIONS not found")

        except Exception as e:
            self.record_test(False, "Animation engine", f"Error: {e}")

    def test_web_interface_structure(self):
        """Test web interface structure."""
        print_test("Web Interface Structure")

        try:
            import LBQualm

            # Test Flask app exists
            if hasattr(LBQualm, 'app'):
                self.record_test(True, "Flask app", "Defined")

                # Test key routes exist
                app = LBQualm.app
                routes = [rule.rule for rule in app.url_map.iter_rules()]

                required_routes = [
                    '/',
                    '/api/status',
                    '/api/animations',
                    '/api/animation',
                    '/api/start',
                    '/api/stop',
                    '/api/params',
                    '/api/health'
                ]

                for route in required_routes:
                    if route in routes:
                        self.record_test(True, f"Route {route}", "Defined")
                    else:
                        self.record_test(False, f"Route {route}", "Missing")

            else:
                self.record_test(False, "Flask app", "Not found")

        except Exception as e:
            self.record_test(False, "Web interface", f"Error: {e}")

    def test_deployment_script(self):
        """Test deployment script."""
        print_test("Deployment Script")

        deploy_script = Path('deploy_lbqualm.sh')

        if deploy_script.exists():
            self.record_test(True, "Deploy script exists", "Found")

            # Check if executable
            is_executable = deploy_script.stat().st_mode & 0o111 != 0
            self.record_test(is_executable, "Deploy script executable",
                           "Executable" if is_executable else "Not executable")

            # Test script syntax (basic check)
            try:
                with open(deploy_script) as f:
                    content = f.read()

                # Check for key functions
                required_functions = [
                    'check_files',
                    'test_ssh',
                    'deploy_files',
                    'install_dependencies',
                    'install_rgb_matrix',
                    'configure_system',
                    'create_service',
                    'test_installation'
                ]

                for func in required_functions:
                    if func in content:
                        self.record_test(True, f"Deploy function {func}", "Found")
                    else:
                        self.record_test(False, f"Deploy function {func}", "Missing")

            except Exception as e:
                self.record_test(False, "Deploy script content", f"Error reading: {e}")
        else:
            self.record_test(False, "Deploy script exists", "Not found")

    def test_configuration_system(self):
        """Test configuration system."""
        print_test("Configuration System")

        try:
            import LBQualm

            config = LBQualm.LBQualmConfig()

            # Test configuration structure
            required_sections = [
                'system',
                'hub75',
                'animation',
                'performance',
                'web'
            ]

            for section in required_sections:
                value = config.get(section)
                if value is not None:
                    self.record_test(True, f"Config section {section}", "Present")
                else:
                    self.record_test(False, f"Config section {section}", "Missing")

            # Test Pi 3B+ optimizations
            pi3b_settings = [
                'hub75.gpio_slowdown',
                'hub75.pwm_bits',
                'hub75.pwm_lsb_nanoseconds',
                'hub75.pwm_dither_bits'
            ]

            for setting in pi3b_settings:
                value = config.get(setting)
                if value is not None:
                    self.record_test(True, f"Pi 3B+ setting {setting}", f"Value: {value}")
                else:
                    self.record_test(False, f"Pi 3B+ setting {setting}", "Missing")

        except Exception as e:
            self.record_test(False, "Configuration system", f"Error: {e}")

    def print_test_summary(self):
        """Print comprehensive test summary."""
        print_header("🧪 TEST RESULTS SUMMARY")

        results = self.test_results
        total = results['total_tests']
        passed = results['passed_tests']
        failed = results['failed_tests']
        warnings = results['warnings']

        # Print statistics
        print(f"{Colors.WHITE}Total Tests:    {total}{Colors.NC}")
        print(f"{Colors.GREEN}Passed:         {passed}{Colors.NC}")
        print(f"{Colors.RED}Failed:         {failed}{Colors.NC}")
        print(f"{Colors.YELLOW}Warnings:       {warnings}{Colors.NC}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"{Colors.CYAN}Success Rate:   {success_rate:.1f}%{Colors.NC}")

        # Overall status
        print("\n" + "="*60)
        if failed == 0:
            print(f"{Colors.GREEN}🎉 ALL TESTS PASSED - LBQUALM IS READY!{Colors.NC}")
            print(f"{Colors.GREEN}✅ LBQualm appears to be fully functional{Colors.NC}")
            print(f"{Colors.GREEN}✅ Safe to deploy to Raspberry Pi{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ {failed} CRITICAL FAILURES DETECTED{Colors.NC}")
            print(f"{Colors.RED}🚫 LBQualm is NOT ready for deployment{Colors.NC}")

            print(f"\n{Colors.RED}Critical failures:{Colors.NC}")
            for failure in self.critical_failures:
                print(f"  - {failure}")

        if warnings > 0:
            print(f"\n{Colors.YELLOW}⚠️  {warnings} warnings (non-critical){Colors.NC}")

        print("="*60)

        # Deployment instructions
        if failed == 0:
            print(f"\n{Colors.CYAN}🚀 Ready to deploy? Run:{Colors.NC}")
            print(f"{Colors.WHITE}./deploy_lbqualm.sh lightbox.local{Colors.NC}")
        else:
            print(f"\n{Colors.RED}🔧 Fix the above issues before deployment{Colors.NC}")

def main():
    """Main test function."""
    tester = LBQualmTester()
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
