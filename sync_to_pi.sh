#!/bin/bash
# sync_to_pi.sh - Script to sync LightBox2.0 to Raspberry Pi

# Configuration - MODIFY THESE VALUES
PI_USER="joshuafield"
PI_HOST="lightbox.local"  # Change to your Pi's hostname or IP
PI_DIR="/home/joshuafield/LightBox2.0"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LightBox2.0 Sync to Raspberry Pi ===${NC}"
echo "Syncing to: ${PI_USER}@${PI_HOST}:${PI_DIR}"

# Check if rsync is installed
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Pi is reachable
echo -e "${YELLOW}Checking if Pi is reachable...${NC}"
ping -c 1 ${PI_HOST} &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Cannot reach ${PI_HOST}. Check connection and hostname/IP.${NC}"
    exit 1
fi

# Create directory on Pi if it doesn't exist
echo -e "${YELLOW}Creating directory on Pi if needed...${NC}"
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_DIR}" || {
    echo -e "${RED}Error: Failed to create directory on Pi. Check SSH connection.${NC}"
    exit 1
}

# Sync files to Pi using rsync
echo -e "${YELLOW}Syncing files to Pi...${NC}"
rsync -avz --exclude 'venv/' \
           --exclude '__pycache__/' \
           --exclude '*.pyc' \
           --exclude '.git/' \
           --exclude 'pi_filesystem/' \
           --exclude '*.bak' \
           --exclude '.DS_Store' \
           --progress ./ ${PI_USER}@${PI_HOST}:${PI_DIR}/ || {
    echo -e "${RED}Error: Failed to sync files to Pi. Check connection and permissions.${NC}"
    exit 1
}

# Setup on Pi
echo -e "${YELLOW}Setting up virtual environment on Pi...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_DIR} && chmod +x setup_venv_pi.sh && ./setup_venv_pi.sh" || {
    echo -e "${RED}Error: Failed to set up virtual environment on Pi.${NC}"
    exit 1
}

echo -e "${GREEN}=== Sync Complete ===${NC}"
echo -e "To run LightBox on your Pi:"
echo -e "  1. SSH to Pi: ${YELLOW}ssh ${PI_USER}@${PI_HOST}${NC}"
echo -e "  2. Navigate to directory: ${YELLOW}cd ${PI_DIR}${NC}"
echo -e "  3. Activate venv: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  4. Run LightBox: ${YELLOW}sudo python main.py${NC}"
echo -e "  5. Access web interface at: ${YELLOW}http://${PI_HOST}:8888${NC}" 