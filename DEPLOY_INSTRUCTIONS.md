# Deploy LightBox to Pi - Manual Instructions

## SSH Access Issue
Your Pi's SSH keys have changed. Here's how to deploy manually:

## Option 1: Direct Copy via Network
1. **On your Pi**, create the directory:
   ```bash
   mkdir -p /home/joshuafield/lightbox
   ```

2. **On your Mac**, copy the file to a USB drive or use network share:
   ```bash
   # Copy to USB drive (if mounted)
   cp lightbox_complete.py /Volumes/USB_DRIVE/
   
   # Or display the file to copy manually
   cat lightbox_complete.py
   ```

3. **On your Pi**, copy from USB and run:
   ```bash
   cp /media/usb/lightbox_complete.py /home/joshuafield/lightbox/
   cd /home/joshuafield/lightbox
   sudo python3 lightbox_complete.py
   ```

## Option 2: Fix SSH and Deploy
1. **On your Pi**, add your Mac's SSH key:
   ```bash
   # On Pi, create SSH directory
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Add your Mac's public key
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILqNjA..." >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

2. **On your Mac**, get your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. **Copy that key** to your Pi's authorized_keys file

4. **Then run deployment**:
   ```bash
   ./deploy_to_pi.sh
   ```

## Option 3: Direct SSH Commands
If you can SSH into your Pi:
```bash
# SSH into Pi
ssh joshuafield@192.168.0.98

# On Pi, download the file
wget http://YOUR_MAC_IP:8080/lightbox_complete.py
# OR paste the file content manually

# Run the system
sudo python3 lightbox_complete.py
```

## Expected Output on Pi
When working, you should see:
```
🚀 Starting Complete LightBox System
==================================================
✅ Configuration loaded - Platform: raspberry_pi
✅ Conductor created
✅ Hardware initialized
   🎯 Matrix: 64x64
   🎬 Embedded animations: ['aurora', 'plasma', 'fire', 'ocean', 'rainbow']
✅ Animation loop started
🌐 Starting web server...
🎯 System ready! You should see lights on the HUB75 matrix!
```

**And your HUB75 matrix should light up with animations!** 