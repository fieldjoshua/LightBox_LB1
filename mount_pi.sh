#!/bin/bash
# Mount Pi filesystem for LightBox deployment
# This script mounts the Raspberry Pi filesystem for direct file operations

set -e

PI_HOST="lightbox.local"
PI_USER="pi"
MOUNT_POINT="/tmp/pi_mount"

echo "🔧 Mounting Pi filesystem..."

# Check if sshfs is installed
if ! command -v sshfs &> /dev/null; then
    echo "❌ sshfs not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install sshfs
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y sshfs
    else
        echo "❌ Unsupported OS. Please install sshfs manually."
        exit 1
    fi
fi

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "📁 Creating mount point: $MOUNT_POINT"
    sudo mkdir -p "$MOUNT_POINT"
fi

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "⚠️  Pi filesystem already mounted at $MOUNT_POINT"
    echo "   To unmount: sudo umount $MOUNT_POINT"
    exit 0
fi

# Test SSH connection
echo "🔍 Testing SSH connection to $PI_USER@$PI_HOST..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$PI_USER@$PI_HOST" exit 2>/dev/null; then
    echo "❌ Cannot connect to $PI_USER@$PI_HOST"
    echo "   Please ensure:"
    echo "   1. Pi is powered on and connected to network"
    echo "   2. SSH is enabled on Pi"
    echo "   3. SSH key authentication is set up"
    echo "   4. Pi hostname 'lightbox.local' resolves correctly"
    exit 1
fi

# Mount Pi filesystem
echo "🔗 Mounting Pi filesystem..."
sshfs "$PI_USER@$PI_HOST:/" "$MOUNT_POINT" -o allow_other,default_permissions

if [ $? -eq 0 ]; then
    echo "✅ Pi filesystem mounted successfully at $MOUNT_POINT"
    echo "📁 Pi home directory: $MOUNT_POINT/home/pi"
    echo "🔧 To unmount later: sudo umount $MOUNT_POINT"
else
    echo "❌ Failed to mount Pi filesystem"
    exit 1
fi

echo ""
echo "🎯 Next steps:"
echo "   1. Run: ./sync_to_pi.sh"
echo "   2. SSH to Pi: ssh pi@lightbox.local"
echo "   3. Run setup: cd ~/LightBox_Organized && ./setup_lightbox_pi.sh" 