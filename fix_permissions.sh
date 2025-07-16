#!/bin/bash
# fix_permissions.sh - Fix permissions for LightBox2.0 on Raspberry Pi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fixing permissions for LightBox2.0 ===${NC}"

# Fix animations directory
echo -e "${YELLOW}Fixing animations directory permissions...${NC}"
sudo mkdir -p animations
sudo chmod -R 777 animations
sudo chown -R root:root animations

# Fix config directory
echo -e "${YELLOW}Fixing config directory permissions...${NC}"
sudo chmod -R 755 config
sudo chmod 644 config/settings.json

# Fix core directory
echo -e "${YELLOW}Fixing core directory permissions...${NC}"
sudo chmod -R 755 core

# Fix drivers directory
echo -e "${YELLOW}Fixing drivers directory permissions...${NC}"
sudo chmod -R 755 drivers

# Fix scripts directory
echo -e "${YELLOW}Fixing scripts directory permissions...${NC}"
sudo chmod -R 755 scripts

# Fix main executable
echo -e "${YELLOW}Fixing main.py permissions...${NC}"
sudo chmod 755 main.py

echo -e "${GREEN}=== Permission fixes complete ===${NC}"
echo -e "You can now run the LightBox2.0 system with: ${YELLOW}sudo python main.py${NC}" 