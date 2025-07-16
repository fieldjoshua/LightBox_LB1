#!/bin/bash
# setup_ssh_pi.sh - Script to set up SSH connection to Raspberry Pi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration - MODIFY THESE VALUES
PI_USER="joshuafield"
PI_HOST="lightbox.local"  # Change to your Pi's hostname or IP

echo -e "${GREEN}=== Setting up SSH connection to Raspberry Pi ===${NC}"
echo -e "This script will help you set up SSH access to your Pi at ${YELLOW}${PI_USER}@${PI_HOST}${NC}"

# Check if ssh-keygen is available
if ! command -v ssh-keygen &> /dev/null; then
    echo -e "${RED}Error: ssh-keygen is not installed. Please install OpenSSH.${NC}"
    exit 1
fi

# Check if the Pi is reachable
echo -e "${YELLOW}Checking if Pi is reachable...${NC}"
ping -c 1 ${PI_HOST} &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Cannot reach ${PI_HOST}. Make sure it's connected to your network.${NC}"
    echo -e "Possible solutions:"
    echo -e "1. Check if the Pi is powered on and connected to the network"
    echo -e "2. Try using the Pi's IP address instead of hostname"
    echo -e "3. Make sure your computer and Pi are on the same network"
    exit 1
fi

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    echo -e "${YELLOW}Generating SSH key...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
else
    echo -e "${YELLOW}SSH key already exists.${NC}"
fi

# Copy SSH key to Pi
echo -e "${YELLOW}Copying SSH key to Pi...${NC}"
echo -e "You'll be prompted for ${PI_USER}'s password on the Pi."

# Use ssh-copy-id if available, otherwise manual method
if command -v ssh-copy-id &> /dev/null; then
    ssh-copy-id ${PI_USER}@${PI_HOST}
else
    # Manual method
    cat ~/.ssh/id_rsa.pub | ssh ${PI_USER}@${PI_HOST} "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
ssh -o BatchMode=yes ${PI_USER}@${PI_HOST} "echo 'SSH connection successful!'"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=== SSH setup complete! ===${NC}"
    echo -e "You can now SSH to your Pi without a password:"
    echo -e "${YELLOW}ssh ${PI_USER}@${PI_HOST}${NC}"
    echo -e "And you can use the sync script to deploy LightBox2.0:"
    echo -e "${YELLOW}./sync_to_pi.sh${NC}"
else
    echo -e "${RED}SSH setup failed. Please try again or set up SSH manually.${NC}"
    exit 1
fi 