#!/bin/bash

# RGB Matrix Library Auto-Installer for LightBox
# Handles all the dependency hell automatically

set -e  # Exit on any error

echo "🚀 Starting RGB Matrix Library Installation"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update -y

# Install all required dependencies
echo -e "${YELLOW}🔧 Installing build dependencies...${NC}"
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

# Clone RGB matrix library if not exists
if [ ! -d "rpi-rgb-led-matrix" ]; then
    echo -e "${YELLOW}📥 Cloning RGB matrix library...${NC}"
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
fi

    cd rpi-rgb-led-matrix

# Clean any previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
make clean || true

# Build the library
echo -e "${YELLOW}⚙️  Building RGB matrix library...${NC}"
make build-python PYTHON=$(which python3)

# Install Python bindings system-wide
echo -e "${YELLOW}📦 Installing Python bindings...${NC}"
cd bindings/python
sudo python3 setup.py install

# Try alternative installation method if first fails
if ! sudo python3 -c "from rgbmatrix import RGBMatrix" 2>/dev/null; then
    echo -e "${YELLOW}🔄 Trying alternative installation method...${NC}"
    cd ../..
    sudo make install-python PYTHON=$(which python3)
fi

# Manual copy as final fallback
if ! sudo python3 -c "from rgbmatrix import RGBMatrix" 2>/dev/null; then
    echo -e "${YELLOW}🔄 Using manual installation fallback...${NC}"
    
    # Find Python version
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_SITE_PACKAGES="/usr/local/lib/python${PYTHON_VERSION}/dist-packages"
    
    # Create directory if it doesn't exist
    sudo mkdir -p "$PYTHON_SITE_PACKAGES"
    
    # Copy the module
    sudo cp -r bindings/python/rgbmatrix "$PYTHON_SITE_PACKAGES/"
    
    # Copy built libraries
    if [ -d "bindings/python/build" ]; then
        sudo find bindings/python/build -name "*.so" -exec cp {} "$PYTHON_SITE_PACKAGES/rgbmatrix/" \;
fi

    # Set permissions
    sudo chmod -R 755 "$PYTHON_SITE_PACKAGES/rgbmatrix"
fi

# Test installation
echo -e "${YELLOW}🧪 Testing installation...${NC}"
if sudo python3 -c "from rgbmatrix import RGBMatrix; print('✅ RGB Matrix library installed successfully!')" 2>/dev/null; then
    echo -e "${GREEN}✅ SUCCESS: RGB Matrix library is working!${NC}"
    echo -e "${GREEN}🎯 Your LightBox hardware should now work properly${NC}"
    
    # Test hardware connection
    echo -e "${YELLOW}🔌 Testing hardware connection...${NC}"
    cd examples-api-use
    if sudo timeout 5 ./demo -D1 --led-rows=64 --led-cols=64 2>/dev/null; then
        echo -e "${GREEN}✅ Hardware test passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Hardware test failed - check your wiring${NC}"
    fi
    
else
    echo -e "${RED}❌ Installation failed. Manual intervention required.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo -e "${GREEN}Run: sudo python3 lightbox_complete.py${NC}"
echo -e "${GREEN}Web interface: http://$(hostname -I | cut -d' ' -f1):8888${NC}"