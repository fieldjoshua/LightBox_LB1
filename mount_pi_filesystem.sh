#!/bin/bash
# Mount Pi filesystem locally for browsing in Cursor

PI_HOST="lightbox.local"
PI_USER="joshuafield"
PI_PATH="/home/joshuafield/LightBox_Organized"
LOCAL_MOUNT_PATH="./pi_filesystem"

echo "🔗 Mounting Pi filesystem for Cursor browsing..."
echo "Pi: $PI_HOST"
echo "Path: $PI_PATH"
echo "Local mount: $LOCAL_MOUNT_PATH"

# Create local mount directory
mkdir -p "$LOCAL_MOUNT_PATH"

# Check if already mounted
if mountpoint -q "$LOCAL_MOUNT_PATH"; then
    echo "⚠️  Already mounted at $LOCAL_MOUNT_PATH"
    echo "To unmount: sudo umount $LOCAL_MOUNT_PATH"
    echo "To browse: open $LOCAL_MOUNT_PATH in Cursor"
    exit 0
fi

# Mount using sshfs
echo "📁 Mounting via SSHFS..."
sshfs "$PI_USER@$PI_HOST:$PI_PATH" "$LOCAL_MOUNT_PATH" -o follow_symlinks,default_permissions

if [ $? -eq 0 ]; then
    echo "✅ Successfully mounted!"
    echo ""
    echo "📂 You can now browse the Pi filesystem in Cursor:"
    echo "   Local path: $LOCAL_MOUNT_PATH"
    echo ""
    echo "🔧 To unmount later:"
    echo "   sudo umount $LOCAL_MOUNT_PATH"
    echo ""
    echo "📋 Quick file list:"
    ls -la "$LOCAL_MOUNT_PATH"
else
    echo "❌ Failed to mount filesystem"
    echo "Make sure sshfs is installed: brew install sshfs"
    exit 1
fi 