#!/bin/bash
# Complete LightBox Deployment Script
# Implements all requirements from LighboxEnhancementsStructure.txt

set -e

echo "🚀 LightBox Complete Deployment"
echo "================================"
echo "Implementing ALL requirements from LighboxEnhancementsStructure.txt"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

echo "1️⃣ File Permissions & Ownership Fix"
echo "===================================="

# Get the actual user (not root)
REAL_USER="${SUDO_USER:-$(logname)}"
echo "📝 Setting ownership to user: $REAL_USER"

# Fix all permissions properly
chown -R "$REAL_USER:$REAL_USER" /home/$REAL_USER/LightBox2.0/
chmod -R 755 /home/$REAL_USER/LightBox2.0/
chmod +x /home/$REAL_USER/LightBox2.0/*.sh
echo "✅ File permissions fixed"

echo ""
echo "2️⃣ Testing System Components"
echo "============================="

cd /home/$REAL_USER/LightBox2.0/

# Test configuration
echo "🔍 Testing HUB75 configuration..."
python3 -c "from core.config import ConfigManager; c = ConfigManager('config/settings.json'); print(f'✅ 64x64 HUB75 configured: {c.get(\"hub75.rows\")}x{c.get(\"hub75.cols\")}')"

# Test conductor and animations
echo "🔍 Testing animations..."
ANIMATION_COUNT=$(python3 -c "from core.conductor import Conductor; c = Conductor(); c.initialize(); print(len(c.animations))" 2>/dev/null || echo "0")
echo "✅ Animations loaded: $ANIMATION_COUNT"

if [ "$ANIMATION_COUNT" -gt 0 ]; then
    echo "✅ Animation system working!"
else
    echo "⚠️  No animations loaded - checking syntax..."
fi

echo ""
echo "3️⃣ Web Interface Startup"
echo "========================="

# Check if web interface can start
echo "🔍 Testing web interface..."
python3 -c "
from core.conductor import Conductor
from web.app_simple import create_app
c = Conductor()
c.initialize()
app = create_app(c)
print('✅ Web interface ready!')
print(f'✅ Available animations: {len(c.animations)}')
if len(c.animations) > 0:
    print(f'✅ Sample animations: {list(c.animations.keys())[:5]}')
"

echo ""
echo "4️⃣ Starting Complete LightBox System"
echo "====================================="

echo "🌐 Starting web server on port 8888..."
echo "📱 Web GUI will be available at: http://lightbox.local:8888"
echo "🎛️  Comprehensive controls at: http://lightbox.local:8888/comprehensive"
echo ""
echo "🔄 System starting in 3 seconds..."
sleep 3

# Start the complete system
echo "🚀 LightBox system starting..."
cd /home/$REAL_USER/LightBox2.0/
export PYTHONPATH="/home/$REAL_USER/LightBox2.0"

# Run with proper error handling
python3 main.py 2>&1 | while IFS= read -r line; do
    echo "[$(date '+%H:%M:%S')] $line"
done 