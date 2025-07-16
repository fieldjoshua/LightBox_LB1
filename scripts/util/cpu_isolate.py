#!/usr/bin/env python3
"""
CPU Isolation Utility for Raspberry Pi.

This script adds or removes 'isolcpus=3' from /boot/cmdline.txt to enable
dedicated CPU core for LED matrix driver. This significantly improves
LED matrix performance and reduces flicker by preventing system processes
from interrupting the matrix refresh thread.

WARNING: This script modifies system files and requires a reboot to take effect.
"""

import os
import sys
import re
import shutil
import argparse
import subprocess
from pathlib import Path

# Constants
CMDLINE_PATH = Path("/boot/cmdline.txt")
BACKUP_PATH = Path("/boot/cmdline.txt.bak")
ISOLCPUS_PARAM = "isolcpus=3"


def check_root():
    """Check if running as root."""
    if os.geteuid() != 0:
        print("Error: This script must be run as root/sudo")
        print("Try: sudo python3 cpu_isolate.py")
        sys.exit(1)


def backup_cmdline():
    """Create a backup of cmdline.txt."""
    if CMDLINE_PATH.exists():
        shutil.copy(CMDLINE_PATH, BACKUP_PATH)
        print(f"Created backup at {BACKUP_PATH}")


def restore_backup():
    """Restore cmdline.txt from backup."""
    if BACKUP_PATH.exists():
        shutil.copy(BACKUP_PATH, CMDLINE_PATH)
        print(f"Restored {CMDLINE_PATH} from backup")
        return True
    else:
        print("No backup file found")
        return False


def is_cpu_isolation_enabled():
    """Check if CPU isolation is enabled in cmdline.txt."""
    if not CMDLINE_PATH.exists():
        return False

    with open(CMDLINE_PATH, "r") as f:
        cmdline = f.read()
        return ISOLCPUS_PARAM in cmdline


def enable_cpu_isolation():
    """Add isolcpus=3 to cmdline.txt."""
    if not CMDLINE_PATH.exists():
        print(f"Error: {CMDLINE_PATH} not found")
        return False

    # Create backup first
    backup_cmdline()

    with open(CMDLINE_PATH, "r") as f:
        cmdline = f.read().strip()

    if ISOLCPUS_PARAM in cmdline:
        print("CPU isolation already enabled")
        return True

    # Add isolcpus=3 at the end
    new_cmdline = cmdline + " " + ISOLCPUS_PARAM

    try:
        with open(CMDLINE_PATH, "w") as f:
            f.write(new_cmdline)
        print("CPU isolation enabled. Please reboot to apply changes.")
        print("  Run: sudo reboot")
        return True
    except Exception as e:
        print(f"Error writing to {CMDLINE_PATH}: {e}")
        restore_backup()
        return False


def disable_cpu_isolation():
    """Remove isolcpus=3 from cmdline.txt."""
    if not CMDLINE_PATH.exists():
        print(f"Error: {CMDLINE_PATH} not found")
        return False

    # Create backup first
    backup_cmdline()

    with open(CMDLINE_PATH, "r") as f:
        cmdline = f.read().strip()

    if ISOLCPUS_PARAM not in cmdline:
        print("CPU isolation already disabled")
        return True

    # Remove isolcpus=3 parameter
    new_cmdline = re.sub(r'\s*isolcpus=3\s*', ' ', cmdline).strip()

    try:
        with open(CMDLINE_PATH, "w") as f:
            f.write(new_cmdline)
        print("CPU isolation disabled. Please reboot to apply changes.")
        print("  Run: sudo reboot")
        return True
    except Exception as e:
        print(f"Error writing to {CMDLINE_PATH}: {e}")
        restore_backup()
        return False


def get_cpu_info():
    """Get CPU information."""
    try:
        cores = 0
        model = "Unknown"
        
        # Get number of cores
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("processor"):
                    cores += 1
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
        
        # Get model from device tree if available
        device_model = Path("/proc/device-tree/model")
        if device_model.exists():
            with open(device_model, "r") as f:
                model = f.read().strip('\0')
        
        return {
            "cores": cores,
            "model": model
        }
    except Exception as e:
        return {
            "cores": "Unknown",
            "model": "Unknown",
            "error": str(e)
        }


def check_cmdline():
    """Check current cmdline.txt content."""
    if CMDLINE_PATH.exists():
        with open(CMDLINE_PATH, "r") as f:
            cmdline = f.read().strip()
            
        cpu_isolated = ISOLCPUS_PARAM in cmdline
        status = "ENABLED" if cpu_isolated else "DISABLED"
        
        print(f"CPU Isolation Status: {status}")
        print(f"Current cmdline.txt: {cmdline}")
        
        return cmdline
    else:
        print(f"Error: {CMDLINE_PATH} not found")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Enable or disable CPU isolation for LED matrix performance"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current CPU isolation status"
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--enable",
        action="store_true", 
        help="Enable CPU isolation (isolcpus=3)"
    )
    group.add_argument(
        "--disable",
        action="store_true",
        help="Disable CPU isolation"
    )
    group.add_argument(
        "--restore",
        action="store_true",
        help="Restore from backup"
    )
    group.add_argument(
        "--info",
        action="store_true",
        help="Show CPU information"
    )
    
    args = parser.parse_args()
    
    # Just info, no root needed
    if args.info:
        cpu_info = get_cpu_info()
        print("CPU Information:")
        print(f"  Model: {cpu_info.get('model', 'Unknown')}")
        print(f"  Cores: {cpu_info.get('cores', 'Unknown')}")
        sys.exit(0)
    
    # Just checking status, no root needed
    if args.check:
        check_cmdline()
        sys.exit(0)
    
    # All other operations require root
    check_root()
    
    if args.enable:
        enable_cpu_isolation()
    elif args.disable:
        disable_cpu_isolation()
    elif args.restore:
        restore_backup()
    else:
        # Default to just checking status
        check_cmdline()


if __name__ == "__main__":
    main() 