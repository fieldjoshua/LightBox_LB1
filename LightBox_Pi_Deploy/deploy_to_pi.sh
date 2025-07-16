#!/bin/bash

# LightBox Complete Deployment Script for Raspberry Pi
# Run this script on the Pi after copying files

set -e  # Exit on any error

echo "🚀 LightBox Pi Deployment Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${RED}❌ This script must be run on a Raspberry Pi${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Raspberry Pi detected${NC}"

# Create project directory
PROJECT_DIR="$HOME/LightBox"
echo -e "${YELLOW}📁 Creating project directory: $PROJECT_DIR${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Copy files if they're in boot partition
if [ -f "/boot/lightbox_complete.py" ]; then
    echo -e "${YELLOW}📦 Moving files from boot partition...${NC}"
    cp /boot/lightbox_complete.py .
    cp /boot/install_rgb_matrix.sh .
    chmod +x install_rgb_matrix.sh
fi

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update -y

# Install Python dependencies in virtual environment
echo -e "${YELLOW}🐍 Installing Python dependencies in venv...${NC}"
pip install flask flask-cors

# Install system dependencies for RGB matrix
echo -e "${YELLOW}🔧 Installing system build dependencies...${NC}"
sudo apt install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    cython3 \
    git \
    cmake \
    libpython3-dev

# Install RGB matrix library
echo -e "${YELLOW}🔌 Installing RGB Matrix library...${NC}"
if [ -f "install_rgb_matrix.sh" ]; then
    # Make sure virtual environment is still active
    source venv/bin/activate
    ./install_rgb_matrix.sh
else
    echo -e "${RED}❌ install_rgb_matrix.sh not found${NC}"
    exit 1
fi

# Create systemd service for auto-start
echo -e "${YELLOW}⚙️  Creating systemd service...${NC}"
sudo tee /etc/systemd/system/lightbox.service > /dev/null << EOF
[Unit]
Description=LightBox LED Matrix Display
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python lightbox_complete.py
Restart=always
RestartSec=10
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable lightbox.service

# Create control scripts
echo -e "${YELLOW}📜 Creating control scripts...${NC}"

# Start script
cat > start_lightbox.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LightBox..."
sudo systemctl start lightbox.service
echo "✅ LightBox started"
echo "🌐 Web interface: http://$(hostname -I | cut -d' ' -f1):8888"
EOF
chmod +x start_lightbox.sh

# Stop script
cat > stop_lightbox.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping LightBox..."
sudo systemctl stop lightbox.service
echo "✅ LightBox stopped"
EOF
chmod +x stop_lightbox.sh

# Status script
cat > status_lightbox.sh << 'EOF'
#!/bin/bash
echo "📊 LightBox Status:"
sudo systemctl status lightbox.service --no-pager
echo ""
echo "🌐 Access at: http://$(hostname -I | cut -d' ' -f1):8888"
EOF
chmod +x status_lightbox.sh

# Manual run script
cat > run_lightbox_manual.sh << 'EOF'
#!/bin/bash
echo "🚀 Running LightBox manually..."
echo "Press Ctrl+C to stop"
sudo python3 lightbox_complete.py
EOF
chmod +x run_lightbox_manual.sh

echo ""
echo -e "${GREEN}🎉 LightBox deployment complete!${NC}"
echo ""
echo -e "${GREEN}📋 Available commands:${NC}"
echo "   ./start_lightbox.sh     - Start LightBox service"
echo "   ./stop_lightbox.sh      - Stop LightBox service"
echo "   ./status_lightbox.sh    - Check status"
echo "   ./run_lightbox_manual.sh - Run manually (for testing)"
echo ""
echo -e "${GREEN}🌐 Web interface will be available at:${NC}"
echo "   http://$(hostname -I | cut -d' ' -f1):8888"
echo "   http://lightbox.local:8888"
echo ""
echo -e "${GREEN}🔧 System service commands:${NC}"
echo "   sudo systemctl start lightbox    - Start service"
echo "   sudo systemctl stop lightbox     - Stop service"
echo "   sudo systemctl restart lightbox  - Restart service"
echo "   sudo systemctl status lightbox   - Check status"
echo ""
echo -e "${YELLOW}💡 The service will auto-start on boot!${NC}"
echo ""
echo -e "${GREEN}🎯 Ready to light up your LEDs!${NC}" 