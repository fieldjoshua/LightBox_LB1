#!/bin/bash
# Deploy Complete LightBox System to Pi

set -e

PI_USER="pi"
PI_HOST="lightbox.local"
PI_PATH="/home/pi/lightbox"

echo "🚀 Deploying Complete LightBox System to Pi..."

# Copy the complete system
echo "📦 Copying lightbox_complete.py to Pi..."
scp lightbox_complete.py ${PI_USER}@${PI_HOST}:${PI_PATH}/

# Copy requirements
echo "📦 Copying requirements..."
scp requirements.txt ${PI_USER}@${PI_HOST}:${PI_PATH}/

# SSH into Pi and run
echo "🔌 Connecting to Pi and starting system..."
ssh ${PI_USER}@${PI_HOST} << 'EOF'
    cd /home/pi/lightbox
    echo "Installing requirements..."
    pip3 install -r requirements.txt
    
    echo "🎯 Starting LightBox with HUB75 matrix..."
    echo "This will show ACTUAL lights on your 64x64 matrix!"
    sudo python3 lightbox_complete.py
EOF

echo "✅ Deployment complete! Your Pi should now show lights!" 