# 🌈 LightBox Pi Complete Deployment Package

This package contains everything needed to deploy a fully functional LightBox LED matrix system on a Raspberry Pi.

## 📦 Package Contents

- `lightbox_complete.py` - Main LightBox system with 14 embedded animations
- `install_rgb_matrix.sh` - Auto-installer for RGB matrix library
- `deploy_to_pi.sh` - Complete deployment script for Pi
- `ssh` - SSH enable file for Pi boot
- `wpa_supplicant.conf.template` - WiFi configuration template
- `setup_sd_card.sh` - SD card preparation script

## 🚀 Quick Start

### Option 1: Fresh Pi Setup (SD Card Method) - **RECOMMENDED**

**✅ Handles modern Pi OS "externally-managed-environment" restrictions automatically**

1. **Flash Raspberry Pi OS** to SD card
2. **Copy files to boot partition:**
   ```bash
   # Copy deployment files to SD card boot partition
   cp lightbox_complete.py /Volumes/bootfs/
   cp install_rgb_matrix.sh /Volumes/bootfs/
   cp deploy_to_pi.sh /Volumes/bootfs/
   cp ssh /Volumes/bootfs/
   
   # Configure WiFi (edit with your credentials)
   cp wpa_supplicant.conf.template /Volumes/bootfs/wpa_supplicant.conf
   # Edit the file with your WiFi name and password
   ```
3. **Boot Pi and SSH in**
4. **Run deployment:**
   ```bash
   chmod +x /boot/deploy_to_pi.sh
   /boot/deploy_to_pi.sh
   ```
   
**What happens during deployment:**
- ✅ Creates isolated Python virtual environment
- ✅ Installs Flask and dependencies in venv (bypasses Pi restrictions)
- ✅ Builds and installs RGB matrix library in venv
- ✅ Creates systemd service with proper venv paths
- ✅ Auto-starts on boot

### Option 2: Existing Pi Setup

1. **Copy files to Pi:**
   ```bash
   scp -r LightBox_Pi_Deploy/* pi@your-pi-ip:~/
   ```
2. **SSH into Pi and deploy:**
   ```bash
   ssh pi@your-pi-ip
   chmod +x deploy_to_pi.sh
   ./deploy_to_pi.sh
   ```

## 🎬 Features

### 14 Built-in Animations
- 🌌 **Aurora** - Northern lights effect
- 🔥 **Plasma** - Psychedelic color waves
- 🔥 **Fire** - Flickering flames
- 🌊 **Ocean** - Rolling ocean waves
- 🌈 **Rainbow** - Moving rainbow patterns
- 🔋 **Matrix** - Digital rain effect
- 🔮 **Kaleidoscope** - Rotating geometric patterns
- ⭐ **Starfield** - 3D space flight
- ☁️ **Clouds** - Peaceful clouds in blue sky
- 🎆 **Fireworks** - Exploding fireworks
- 🚀 **Hyperspace** - 120 BPM space thrust
- 🌀 **Golden Ratio** - Mathematical spirals
- ✨ **Dust** - Floating particles
- 🌧️ **Rain** - Raindrops with lightning

### Web Interface Controls
- **Animation Selection** - Switch between 14 animations
- **Brightness Control** - 10-100% brightness
- **Speed Control** - 10-200% animation speed
- **Color Controls** - Hue, saturation, primary color
- **Advanced Settings** - Scale, complexity, smoothness
- **Preset Management** - Save/load configurations

## 🔧 Hardware Requirements

- **Raspberry Pi 3B+/4** (recommended)
- **HUB75 LED Matrix** (64x64 recommended)
- **5V Power Supply** for LED matrix (separate from Pi)
- **Adafruit RGB Matrix HAT** (optional but recommended)

## 🌐 Network Access

After deployment, access your LightBox at:
- `http://lightbox.local:8888`
- `http://[pi-ip-address]:8888`

Works on any device: phones, tablets, laptops!

## ⚙️ Service Management

The system installs as a systemd service for auto-start on boot:

```bash
# Control scripts (created by deployment)
./start_lightbox.sh      # Start service
./stop_lightbox.sh       # Stop service
./status_lightbox.sh     # Check status
./run_lightbox_manual.sh # Run manually for testing

# Direct systemctl commands
sudo systemctl start lightbox
sudo systemctl stop lightbox
sudo systemctl restart lightbox
sudo systemctl status lightbox
```

## 🔌 Hardware Wiring

Connect HUB75 matrix to Pi GPIO pins:

| HUB75 Pin | Pi GPIO Pin |
|-----------|-------------|
| R1        | GPIO 11     |
| G1        | GPIO 12     |
| B1        | GPIO 13     |
| R2        | GPIO 15     |
| G2        | GPIO 16     |
| B2        | GPIO 18     |
| A         | GPIO 7      |
| B         | GPIO 8      |
| C         | GPIO 9      |
| D         | GPIO 10     |
| CLK       | GPIO 23     |
| STB/LAT   | GPIO 24     |
| OE        | GPIO 25     |
| GND       | GND         |

## 🛠️ Troubleshooting

### Pi Not Found on Network
```bash
# Scan network for Pi
nmap -sn 192.168.1.0/24 | grep -B2 -A2 "Raspberry"

# Try different hostnames
ping raspberrypi.local
ping lightbox.local
```

### SSH Connection Issues
```bash
# Check if SSH is enabled
sudo systemctl status ssh

# Enable SSH if needed
sudo systemctl enable ssh
sudo systemctl start ssh
```

### RGB Matrix Not Working
```bash
# Check if library is installed
python3 -c "from rgbmatrix import RGBMatrix; print('Works!')"

# Reinstall library
./install_rgb_matrix.sh
```

### Web Interface Not Loading
```bash
# Check service status
sudo systemctl status lightbox

# Check logs
sudo journalctl -u lightbox -f

# Manual run for debugging
sudo python3 lightbox_complete.py
```

## 📊 Performance Optimization

For best performance:
1. **Disable audio:** Add `dtparam=audio=off` to `/boot/config.txt`
2. **Set GPU memory:** Add `gpu_mem=16` to `/boot/config.txt`
3. **CPU isolation:** Add `isolcpus=3` to `/boot/cmdline.txt`

## 🔐 Security Notes

- Change default Pi password: `passwd`
- Update system: `sudo apt update && sudo apt upgrade`
- Consider firewall: `sudo ufw enable`

## 📈 System Requirements

- **Minimum:** Pi 3B+ with 1GB RAM
- **Recommended:** Pi 4 with 2GB+ RAM
- **Storage:** 8GB+ SD card (Class 10)
- **Power:** 5V 3A for Pi + separate PSU for matrix

## 🆘 Support

For issues:
1. Check service logs: `sudo journalctl -u lightbox`
2. Run manual mode: `./run_lightbox_manual.sh`
3. Verify hardware connections
4. Check network connectivity

## 🎯 Quick Reference

```bash
# Status check
./status_lightbox.sh

# Start/stop
./start_lightbox.sh
./stop_lightbox.sh

# Access web interface
http://lightbox.local:8888

# View logs
sudo journalctl -u lightbox -f

# Manual run
sudo python3 lightbox_complete.py
```

---

**🎉 Enjoy your LightBox LED matrix display!** 