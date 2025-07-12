#!/bin/bash
# Pi filesystem browser helper

PI_MOUNT="./pi_filesystem"

echo "🔍 Pi Filesystem Browser"
echo "========================"
echo ""

if [ ! -d "$PI_MOUNT" ]; then
    echo "❌ Pi filesystem not mounted"
    echo "Run: ./mount_pi_filesystem.sh"
    exit 1
fi

echo "📂 Mounted at: $PI_MOUNT"
echo ""

# Show main directories
echo "📁 Main directories:"
ls -la "$PI_MOUNT" | grep "^d" | awk '{print "  " $9}'
echo ""

# Show key files
echo "📄 Key files:"
ls -la "$PI_MOUNT"/*.py 2>/dev/null | head -5 | awk '{print "  " $9}'
echo ""

echo "🔧 Commands:"
echo "  Browse in Cursor: open $PI_MOUNT"
echo "  List all files: ls -la $PI_MOUNT"
echo "  Unmount: sudo umount $PI_MOUNT"
echo "  Remount: ./mount_pi_filesystem.sh"
echo ""

# Check if Cursor is available
if command -v cursor &> /dev/null; then
    echo "🚀 Quick open in Cursor:"
    echo "  cursor $PI_MOUNT"
    echo ""
fi

echo "💡 Tip: You can now use Cursor's file finder to browse your Pi's files!" 