#!/bin/bash
#
# LightBox HUB75 RGB Matrix Library Installation Script
# Installs Henner Zeller's rpi-rgb-led-matrix library with Python bindings
#

set -e  # Exit on error

echo "================================================"
echo "LightBox HUB75 RGB Matrix Library Installer"
echo "================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash install_rgb_matrix.sh"
    exit 1
fi

# Detect Raspberry Pi model
PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | cut -d ':' -f 2 | xargs)
echo "Detected: $PI_MODEL"
echo ""

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
apt-get install -y \
    git \
    python3-dev \
    python3-pillow \
    python3-numpy \
    build-essential \
    libgraphicsmagick++-dev \
    libwebp-dev

# Create temporary directory
TEMP_DIR="/tmp/rgb-matrix-install"
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Clone the repository
echo ""
echo "📥 Cloning rpi-rgb-led-matrix repository..."
if [ -d "rpi-rgb-led-matrix" ]; then
    echo "Repository already exists, updating..."
    cd rpi-rgb-led-matrix
    git pull
else
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
    cd rpi-rgb-led-matrix
fi

# Build the library
echo ""
echo "🔨 Building C++ library..."
make -j$(nproc)

# Build Python bindings
echo ""
echo "🐍 Building Python bindings..."
make build-python PYTHON=$(which python3)

# Install Python bindings
echo ""
echo "📦 Installing Python bindings..."
make install-python PYTHON=$(which python3)

# Configure system for optimal performance
echo ""
echo "⚙️  Configuring system for optimal performance..."

# Disable audio (conflicts with PWM)
echo "   - Disabling audio..."
if ! grep -q "dtparam=audio=off" /boot/config.txt; then
    echo "dtparam=audio=off" >> /boot/config.txt
fi

# Set GPU memory split
echo "   - Setting GPU memory to 16MB..."
if ! grep -q "gpu_mem=" /boot/config.txt; then
    echo "gpu_mem=16" >> /boot/config.txt
else
    sed -i 's/gpu_mem=.*/gpu_mem=16/' /boot/config.txt
fi

# Optional: Disable Bluetooth on Pi 3/4
if [[ "$PI_MODEL" == *"Pi 3"* ]] || [[ "$PI_MODEL" == *"Pi 4"* ]]; then
    read -p "Disable Bluetooth for better performance? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   - Disabling Bluetooth..."
        if ! grep -q "dtoverlay=disable-bt" /boot/config.txt; then
            echo "dtoverlay=disable-bt" >> /boot/config.txt
        fi
        systemctl disable bluetooth
    fi
fi

# Optional: CPU isolation for best performance
echo ""
read -p "Enable CPU isolation for best performance? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   - Configuring CPU isolation..."
    if ! grep -q "isolcpus=" /boot/cmdline.txt; then
        sed -i '$ s/$/ isolcpus=3/' /boot/cmdline.txt
        echo "   ✅ CPU core 3 will be isolated on next reboot"
    else
        echo "   ℹ️  CPU isolation already configured"
    fi
fi

# Create udev rule for non-root access (optional)
echo ""
read -p "Create udev rule for non-root GPIO access? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   - Creating udev rule..."
    cat > /etc/udev/rules.d/99-gpio.rules << EOF
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
SUBSYSTEM=="bcm2835-gpiomem", GROUP="gpio", MODE="0660"
EOF
    
    # Add current user to gpio group
    CURRENT_USER=$(who am i | awk '{print $1}')
    usermod -a -G gpio $CURRENT_USER
    echo "   ✅ Added $CURRENT_USER to gpio group"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
cd $TEMP_DIR/rpi-rgb-led-matrix/bindings/python/samples
python3 -c "import rgbmatrix; print('✅ rgbmatrix module imported successfully')"

# Install additional Python packages
echo ""
echo "📦 Installing additional Python packages..."
pip3 install --upgrade pillow numpy

# Create example configuration
echo ""
echo "📝 Creating example configuration..."
EXAMPLE_CONFIG="/tmp/hub75_example_config.json"
cat > $EXAMPLE_CONFIG << EOF
{
  "matrix_type": "HUB75",
  "matrix_width": 64,
  "matrix_height": 64,
  "brightness": 0.75,
  "fps": 30,
  "hub75_settings": {
    "rows": 64,
    "cols": 64,
    "chain_length": 1,
    "parallel": 1,
    "pwm_bits": 11,
    "gpio_slowdown": 4,
    "hardware_mapping": "adafruit-hat",
    "disable_hardware_pulsing": false
  }
}
EOF

echo "   Example configuration saved to: $EXAMPLE_CONFIG"

# Summary
echo ""
echo "================================================"
echo "✅ Installation completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Connect your HUB75 panel and power supply"
echo "2. Reboot to apply system changes:"
echo "   sudo reboot"
echo "3. Test your panel with:"
echo "   cd $TEMP_DIR/rpi-rgb-led-matrix/bindings/python/samples"
echo "   sudo python3 runtext.py --led-rows=64 --led-cols=64"
echo ""
echo "For LightBox:"
echo "1. Run the migration script:"
echo "   python3 scripts/migrate_to_hub75.py"
echo "2. Start LightBox with HUB75 support:"
echo "   sudo python3 LightBox/LB_Interface/LightBox/Conductor.py"
echo ""
echo "⚠️  Remember:"
echo "- HUB75 panels require separate 5V power supply"
echo "- Always run with sudo for GPIO access"
echo "- See documentation/HUB75_SETUP_GUIDE.md for details"
echo ""

# Clean up
cd /
rm -rf $TEMP_DIR

echo "Installation complete!"