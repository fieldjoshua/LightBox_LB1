# Deploy to Raspberry Pi from GitHub

## Method 1: Direct Clone on Pi (Recommended)

SSH into your Pi and clone directly:

```bash
# SSH to your Pi
ssh fieldjoshua@192.168.0.222

# Navigate to where you want the code (e.g., home directory)
cd ~

# Clone your repository
git clone https://github.com/fieldjoshua/LightBox_2.0.git

# Enter the directory
cd LightBox_2.0

# Install dependencies
pip install -r requirements-optimized.txt

# For HUB75 support (if needed)
sudo bash scripts/install_rgb_matrix.sh

# Run the migration script if you have existing settings
python3 scripts/migrate_to_optimized.py

# Test it out
sudo python3 lightbox.py
```

## Method 2: Update Existing Installation

If you already have LightBox on your Pi:

```bash
# SSH to your Pi
ssh fieldjoshua@192.168.0.222

# Backup existing installation
cd ~/LightBox
tar -czf ~/lightbox_backup_$(date +%Y%m%d).tar.gz .

# Option A: Fresh clone (recommended)
cd ~
mv LightBox LightBox_old
git clone https://github.com/fieldjoshua/LightBox_2.0.git LightBox
cd LightBox

# Option B: Add as new remote (if you want to keep history)
git remote add optimized https://github.com/fieldjoshua/LightBox_2.0.git
git fetch optimized
git checkout optimized/main -b optimized-version
```

## Method 3: Quick Deploy Script

Create this on your local machine:

```bash
#!/bin/bash
# deploy_to_pi.sh

PI_HOST="fieldjoshua@192.168.0.222"
PI_DIR="~/LightBox_2.0"

echo "Deploying to Pi at $PI_HOST..."

ssh $PI_HOST << 'EOF'
  # Backup if exists
  if [ -d ~/LightBox_2.0 ]; then
    echo "Backing up existing installation..."
    mv ~/LightBox_2.0 ~/LightBox_2.0.backup.$(date +%Y%m%d_%H%M%S)
  fi
  
  # Clone fresh
  echo "Cloning repository..."
  git clone https://github.com/fieldjoshua/LightBox_2.0.git ~/LightBox_2.0
  
  cd ~/LightBox_2.0
  
  # Install dependencies
  echo "Installing dependencies..."
  pip3 install -r requirements-optimized.txt
  
  echo "Deployment complete!"
  echo "To run: cd ~/LightBox_2.0 && sudo python3 lightbox.py"
EOF
```

## Post-Deployment Steps

1. **Set up as service (optional)**:
   ```bash
   sudo cp lightbox.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable lightbox
   sudo systemctl start lightbox
   ```

2. **Platform-specific optimizations**:
   
   For Pi 3B+ with HUB75:
   ```bash
   # Add to /boot/cmdline.txt: isolcpus=3
   # Add to /boot/config.txt: gpu_mem=16
   sudo nano /boot/cmdline.txt
   # Reboot after changes
   ```

3. **Test the deployment**:
   ```bash
   # Test in simulation first
   python3 run_simulation.py
   
   # Then with hardware
   sudo python3 lightbox.py
   
   # Check web interface
   # http://192.168.0.222:5001
   ```

## Updating from GitHub

Once deployed, updating is easy:

```bash
cd ~/LightBox_2.0
git pull origin main
# Restart the service or application
```

## Troubleshooting

- **Permission denied**: Make sure to use `sudo` for hardware access
- **Missing dependencies**: Some might need system packages:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-pip python3-venv
  ```
- **GPIO errors**: Ensure you're in the gpio group:
  ```bash
  sudo usermod -a -G gpio $USER
  # Log out and back in
  ```