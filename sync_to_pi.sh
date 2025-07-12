#!/bin/bash
# Sync LightBox Organized project to Raspberry Pi
# This script syncs the project files to the Pi for deployment

set -e

PI_HOST="lightbox.local"
PI_USER="pi"
PI_PROJECT_DIR="~/LightBox_Organized"
MOUNT_POINT="/tmp/pi_mount"

echo "🚀 Syncing LightBox Organized to Pi..."

# Check if Pi filesystem is mounted
if ! mountpoint -q "$MOUNT_POINT"; then
    echo "❌ Pi filesystem not mounted. Run ./mount_pi.sh first."
    exit 1
fi

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$PI_USER@$PI_HOST" exit 2>/dev/null; then
    echo "❌ Cannot connect to $PI_USER@$PI_HOST"
    exit 1
fi

# Create project directory on Pi
echo "📁 Creating project directory on Pi..."
ssh "$PI_USER@$PI_HOST" "mkdir -p $PI_PROJECT_DIR"

# Sync project files (excluding unnecessary files)
echo "📤 Syncing project files..."
rsync -av --progress \
    --exclude='.git/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='*.log' \
    --exclude='.vscode/' \
    --exclude='.idea/' \
    --exclude='*.tmp' \
    --exclude='*.temp' \
    --exclude='.cache/' \
    --exclude='htmlcov/' \
    --exclude='.coverage' \
    --exclude='.pytest_cache/' \
    --exclude='.mypy_cache/' \
    --exclude='.pyre/' \
    --exclude='*.egg-info/' \
    --exclude='build/' \
    --exclude='dist/' \
    --exclude='downloads/' \
    --exclude='eggs/' \
    --exclude='parts/' \
    --exclude='sdist/' \
    --exclude='var/' \
    --exclude='wheels/' \
    --exclude='.installed.cfg' \
    --exclude='MANIFEST' \
    --exclude='*.egg' \
    --exclude='.Python' \
    --exclude='lib/' \
    --exclude='lib64/' \
    --exclude='develop-eggs/' \
    --exclude='.eggs/' \
    --exclude='env.bak/' \
    --exclude='venv.bak/' \
    --exclude='.env' \
    --exclude='config/local_settings.json' \
    --exclude='*.bin' \
    --exclude='*.hex' \
    --exclude='*.service' \
    --exclude='install_rgb_matrix.sh' \
    ./ "$PI_USER@$PI_HOST:$PI_PROJECT_DIR/"

if [ $? -eq 0 ]; then
    echo "✅ Project files synced successfully!"
else
    echo "❌ Failed to sync project files"
    exit 1
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
ssh "$PI_USER@$PI_HOST" "chmod +x $PI_PROJECT_DIR/*.sh"
ssh "$PI_USER@$PI_HOST" "chmod +x $PI_PROJECT_DIR/main.py"
ssh "$PI_USER@$PI_HOST" "chmod +x $PI_PROJECT_DIR/lightbox.py"

# Create virtual environment on Pi if it doesn't exist
echo "🐍 Setting up Python environment..."
ssh "$PI_USER@$PI_HOST" "cd $PI_PROJECT_DIR && python3 -m venv venv"

# Install dependencies
echo "📦 Installing Python dependencies..."
ssh "$PI_USER@$PI_HOST" "cd $PI_PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

echo ""
echo "🎉 Sync complete! Next steps:"
echo "   1. SSH to Pi: ssh pi@lightbox.local"
echo "   2. Run setup: cd ~/LightBox_Organized && ./setup_lightbox_pi.sh"
echo "   3. Or run directly: cd ~/LightBox_Organized && python3 main.py" 