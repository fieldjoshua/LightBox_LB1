#!/bin/bash
# Deploy LightBox Optimizations to Pi
# Works with Tailscale, local network, or direct IP

set -e

# Configuration - MODIFY THESE AS NEEDED
PI_USER="joshuafield"
PI_HOST=""  # Will be detected or prompted
PI_DIR="/home/joshuafield/LightBox2.0"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🎯 LightBox Optimization Deployment${NC}"
echo -e "${BLUE}This will deploy the anti-jitter fixes to your Pi${NC}"

# Function to test SSH connection
test_ssh() {
    local host=$1
    echo -e "${YELLOW}Testing connection to $host...${NC}"
    ssh -o ConnectTimeout=5 -o BatchMode=yes ${PI_USER}@${host} "echo 'Connection successful'" 2>/dev/null
}

# Try to detect Pi address
detect_pi() {
    echo -e "${YELLOW}🔍 Detecting Pi address...${NC}"
    
    # Try Tailscale first
    if command -v tailscale &> /dev/null; then
        echo "Checking Tailscale..."
        TAILSCALE_DEVICES=$(tailscale status --json 2>/dev/null | jq -r '.Peer[] | select(.HostName | contains("lightbox") or contains("pi") or contains("raspberry")) | .DNSName' 2>/dev/null || echo "")
        if [ ! -z "$TAILSCALE_DEVICES" ]; then
            for device in $TAILSCALE_DEVICES; do
                echo "Found potential device: $device"
                if test_ssh $device; then
                    PI_HOST=$device
                    echo -e "${GREEN}✅ Connected via Tailscale: $PI_HOST${NC}"
                    return 0
                fi
            done
        fi
    fi
    
    # Try common local addresses
    echo "Checking local network..."
    for addr in "lightbox.local" "raspberrypi.local" "pi.local"; do
        if test_ssh $addr; then
            PI_HOST=$addr
            echo -e "${GREEN}✅ Connected via local network: $PI_HOST${NC}"
            return 0
        fi
    done
    
    return 1
}

# Get Pi address
if [ -z "$PI_HOST" ]; then
    if ! detect_pi; then
        echo -e "${YELLOW}Could not auto-detect Pi. Please enter details:${NC}"
        read -p "Pi hostname or IP address: " PI_HOST
        read -p "Pi username (default: joshuafield): " input_user
        if [ ! -z "$input_user" ]; then
            PI_USER=$input_user
        fi
    fi
fi

# Verify connection
if ! test_ssh $PI_HOST; then
    echo -e "${RED}❌ Cannot connect to ${PI_USER}@${PI_HOST}${NC}"
    echo "Make sure:"
    echo "  1. Tailscale is running on both devices"
    echo "  2. SSH is enabled on Pi"
    echo "  3. Correct username/hostname"
    exit 1
fi

echo -e "${GREEN}🔗 Connected to ${PI_USER}@${PI_HOST}${NC}"

# Create backup of current config
echo -e "${YELLOW}📋 Creating backup of current config...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && cp config/settings.json config/settings_backup_$(date +%Y%m%d_%H%M%S).json" || true

# Deploy optimization files
echo -e "${YELLOW}📦 Deploying optimization files...${NC}"

# Copy main optimization script
scp optimize_lightbox_performance.py ${PI_USER}@${PI_HOST}:${PI_DIR}/

# Copy optimized configuration
scp config/settings_optimized.json ${PI_USER}@${PI_HOST}:${PI_DIR}/config/

# Copy test script
scp test_optimizations.py ${PI_USER}@${PI_HOST}:${PI_DIR}/

# Copy audit report
scp LIGHTBOX_AUDIT_FIXES_REPORT.md ${PI_USER}@${PI_HOST}:${PI_DIR}/

# Update main config with optimizations
echo -e "${YELLOW}⚙️  Applying optimized configuration...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && cp config/settings_optimized.json config/settings.json"

# Run optimization script on Pi
echo -e "${YELLOW}🔧 Running optimization script on Pi...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && python3 optimize_lightbox_performance.py"

# Test the optimizations
echo -e "${YELLOW}🧪 Testing optimizations...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && python3 test_optimizations.py"

echo -e "${GREEN}✅ Optimization deployment complete!${NC}"
echo ""
echo -e "${BLUE}📊 What was fixed:${NC}"
echo "  • PWM bits: 11 → 8 (better refresh rate)"
echo "  • GPIO slowdown: 4 → 2 (faster updates)"
echo "  • Hardware PWM: enabled (smoother rendering)"
echo "  • Double buffering: implemented"
echo "  • CPU isolation: configured"
echo ""
echo -e "${YELLOW}🎮 Next steps:${NC}"
echo "1. Restart your LightBox:"
echo "   ${PI_USER}@${PI_HOST}: sudo systemctl restart lightbox"
echo ""
echo "2. Monitor performance:"
echo "   ${PI_USER}@${PI_HOST}: cd ${PI_DIR} && python3 test_optimizations.py"
echo ""
echo "3. Access web interface at: http://${PI_HOST}:8888"
echo ""
echo -e "${GREEN}🎉 Your animations should now be much smoother!${NC}" 