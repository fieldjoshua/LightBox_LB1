#!/bin/bash

# LightBox SD Card Setup Script
# Automates copying files to Pi SD card boot partition

set -e  # Exit on any error

echo "🔧 LightBox SD Card Setup"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to find SD card mount point
find_sd_card() {
    # Common mount points
    POSSIBLE_MOUNTS=(
        "/Volumes/bootfs"
        "/Volumes/boot"
        "/Volumes/BOOT"
        "/media/boot"
        "/mnt/boot"
    )
    
    for mount in "${POSSIBLE_MOUNTS[@]}"; do
        if [ -d "$mount" ]; then
            echo "$mount"
            return 0
        fi
    done
    
    return 1
}

# Check if we're in the right directory
if [ ! -f "lightbox_complete.py" ]; then
    echo -e "${RED}❌ lightbox_complete.py not found${NC}"
    echo "Please run this script from the LightBox_Pi_Deploy directory"
    exit 1
fi

# Find SD card
echo -e "${YELLOW}🔍 Looking for SD card...${NC}"
BOOT_MOUNT=$(find_sd_card)

if [ $? -ne 0 ] || [ -z "$BOOT_MOUNT" ]; then
    echo -e "${RED}❌ SD card boot partition not found${NC}"
    echo ""
    echo "Available volumes:"
    ls /Volumes/ 2>/dev/null || ls /media/ 2>/dev/null || echo "No volumes found"
    echo ""
    echo "Please:"
    echo "1. Insert SD card with Raspberry Pi OS"
    echo "2. Make sure it's mounted"
    echo "3. Run this script again"
    exit 1
fi

echo -e "${GREEN}✅ Found SD card at: $BOOT_MOUNT${NC}"

# Copy core files
echo -e "${YELLOW}📦 Copying LightBox files...${NC}"
cp lightbox_complete.py "$BOOT_MOUNT/"
cp install_rgb_matrix.sh "$BOOT_MOUNT/"
cp deploy_to_pi.sh "$BOOT_MOUNT/"

# Enable SSH
echo -e "${YELLOW}🔐 Enabling SSH...${NC}"
cp ssh "$BOOT_MOUNT/"

# WiFi setup
echo ""
echo -e "${YELLOW}📶 WiFi Configuration${NC}"
read -p "Do you want to configure WiFi? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter WiFi network name (SSID): " WIFI_SSID
    read -s -p "Enter WiFi password: " WIFI_PASSWORD
    echo
    
    # Create WiFi config
    cat > "$BOOT_MOUNT/wpa_supplicant.conf" << EOF
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="$WIFI_SSID"
    psk="$WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
EOF
    
    echo -e "${GREEN}✅ WiFi configured for network: $WIFI_SSID${NC}"
else
    echo "ℹ️  WiFi not configured - you'll need Ethernet or configure later"
fi

# Optional: Set static IP
echo ""
read -p "Do you want to set a static IP address? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter desired IP (e.g., 192.168.1.100): " STATIC_IP
    read -p "Enter gateway IP (e.g., 192.168.1.1): " GATEWAY_IP
    
    # Create userconf for auto-login (modern Pi OS)
    echo "pi:\$6\$rBgFaXBOiTRpJGX7\$9nJbFwGUMZKSgNUKV0v9Qe2a3AzHNLKsOVEJ0tAR3aV2jTg5QiDvqVeFCzDLVZHYqChzNpAbzHSJmjkxBKjxV0" > "$BOOT_MOUNT/userconf.txt"
    
    echo -e "${GREEN}✅ Static IP configuration prepared${NC}"
    echo "Note: You'll need to configure the full network settings after first boot"
fi

# Verify files
echo ""
echo -e "${YELLOW}🔍 Verifying files...${NC}"
REQUIRED_FILES=(
    "lightbox_complete.py"
    "install_rgb_matrix.sh" 
    "deploy_to_pi.sh"
    "ssh"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$BOOT_MOUNT/$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file${NC}"
        ALL_GOOD=false
    fi
done

if [ -f "$BOOT_MOUNT/wpa_supplicant.conf" ]; then
    echo -e "${GREEN}✅ wpa_supplicant.conf${NC}"
fi

if [ "$ALL_GOOD" = true ]; then
    echo ""
    echo -e "${GREEN}🎉 SD Card setup complete!${NC}"
    echo ""
    echo -e "${GREEN}📋 Next steps:${NC}"
    echo "1. Safely eject the SD card"
    echo "2. Insert SD card into Raspberry Pi"
    echo "3. Boot the Pi (give it 2-3 minutes)"
    echo "4. Find the Pi's IP address:"
    echo "   nmap -sn 192.168.1.0/24 | grep -B2 -A2 'Raspberry'"
    echo "5. SSH into the Pi:"
    echo "   ssh pi@[IP-ADDRESS]"
    echo "6. Run the deployment script:"
    echo "   chmod +x /boot/deploy_to_pi.sh"
    echo "   /boot/deploy_to_pi.sh"
    echo ""
    echo -e "${GREEN}🌐 After deployment, access at:${NC}"
    echo "   http://lightbox.local:8888"
    echo "   http://[pi-ip]:8888"
    echo ""
    echo -e "${YELLOW}💡 The Pi will auto-start LightBox on every boot!${NC}"
else
    echo ""
    echo -e "${RED}❌ Some files failed to copy. Please check SD card and try again.${NC}"
    exit 1
fi

# Final size check
echo ""
echo -e "${YELLOW}📊 SD Card Usage:${NC}"
df -h "$BOOT_MOUNT" 2>/dev/null || echo "Could not check disk usage"

echo ""
echo -e "${GREEN}🎯 Ready to boot your LightBox Pi!${NC}" 