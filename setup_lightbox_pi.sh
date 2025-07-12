#!/bin/bash
# Setup LightBox Organized on Raspberry Pi
# This script configures the LightBox system on the Pi

set -e

echo "🔧 Setting up LightBox Organized on Raspberry Pi..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This script is designed to run on Raspberry Pi"
    echo "   Current system: $(uname -a)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libjasper-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libatlas-base-dev \
    libjasper-dev \
    libqtcore4 \
    libqt4-test \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libatlas-base-dev \
    libjasper-dev \
    libqtcore4 \
    libqt4-test

# Install HUB75 RGB Matrix library
echo "🎨 Installing HUB75 RGB Matrix library..."
if [ ! -d "/opt/rgb-matrix" ]; then
    cd /opt
    sudo git clone https://github.com/hzeller/rpi-rgb-led-matrix.git rgb-matrix
    cd rgb-matrix
    sudo make build-python PYTHON=$(which python3)
    sudo make install-python PYTHON=$(which python3)
else
    echo "✅ HUB75 library already installed"
fi

# Configure GPIO for hardware PWM (if not already done)
echo "⚡ Configuring GPIO for hardware PWM..."
if ! grep -q "dtoverlay=pwm" /boot/config.txt; then
    echo "dtparam=audio=off" | sudo tee -a /boot/config.txt
    echo "dtoverlay=pwm-2chan,pin=18,func=2,pin2=13,func2=4" | sudo tee -a /boot/config.txt
    echo "✅ Hardware PWM configured"
else
    echo "✅ Hardware PWM already configured"
fi

# Configure CPU isolation for better performance
echo "🚀 Configuring CPU isolation..."
if ! grep -q "isolcpus=3" /boot/cmdline.txt; then
    sudo sed -i 's/$/ isolcpus=3/' /boot/cmdline.txt
    echo "✅ CPU isolation configured"
else
    echo "✅ CPU isolation already configured"
fi

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd ~/LightBox_Organized
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for HUB75
echo "🎨 Installing HUB75 Python bindings..."
pip install rpi-rgb-led-matrix

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/lightbox.service > /dev/null <<EOF
[Unit]
Description=LightBox Organized LED Matrix Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/LightBox_Organized
Environment=PATH=/home/pi/LightBox_Organized/venv/bin
ExecStart=/home/pi/LightBox_Organized/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Enabling LightBox service..."
sudo systemctl daemon-reload
sudo systemctl enable lightbox.service

# Set up web interface
echo "🌐 Configuring web interface..."
if ! grep -q "lightbox.local" /etc/hosts; then
    echo "127.0.0.1 lightbox.local" | sudo tee -a /etc/hosts
fi

# Create startup script
echo "📝 Creating startup script..."
cat > ~/start_lightbox.sh << 'EOF'
#!/bin/bash
cd ~/LightBox_Organized
source venv/bin/activate
python main.py
EOF

chmod +x ~/start_lightbox.sh

# Create test script
echo "🧪 Creating test script..."
cat > ~/test_lightbox.sh << 'EOF'
#!/bin/bash
cd ~/LightBox_Organized
source venv/bin/activate
python test_system.py
EOF

chmod +x ~/test_lightbox.sh

# Configure firewall for web interface
echo "🔥 Configuring firewall..."
sudo ufw allow 5000/tcp
sudo ufw allow ssh

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/lightbox > /dev/null <<EOF
/home/pi/LightBox_Organized/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 pi pi
}
EOF

# Create configuration backup
echo "💾 Creating configuration backup..."
cp config/settings.json config/settings.json.backup

echo ""
echo "🎉 LightBox Organized setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Reboot Pi: sudo reboot"
echo "   2. Start service: sudo systemctl start lightbox"
echo "   3. Check status: sudo systemctl status lightbox"
echo "   4. View logs: sudo journalctl -u lightbox -f"
echo "   5. Access web interface: http://lightbox.local:5000"
echo "   6. Test system: ./test_lightbox.sh"
echo ""
echo "🔧 Manual start: cd ~/LightBox_Organized && source venv/bin/activate && python main.py"
echo "🌐 Web interface: http://$(hostname -I | awk '{print $1}'):5000" 