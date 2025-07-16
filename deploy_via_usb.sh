#!/bin/bash
# Deploy LightBox Optimizations via USB Drive
# For when network connectivity is problematic

echo "📦 Creating USB deployment package..."

# Create deployment directory
mkdir -p lightbox_optimizations
cd lightbox_optimizations

# Copy all optimization files
cp ../optimize_lightbox_performance.py .
cp ../test_optimizations.py .
cp ../config/settings_optimized.json .
cp ../LIGHTBOX_AUDIT_FIXES_REPORT.md .

# Create installation script for Pi
cat > install_on_pi.sh << 'EOF'
#!/bin/bash
# Run this script ON THE PI to install optimizations

echo "🎯 Installing LightBox Optimizations on Pi..."

# Backup current config
cp /home/pi/LightBox2.0/config/settings.json /home/pi/LightBox2.0/config/settings_backup_$(date +%Y%m%d_%H%M%S).json

# Copy optimization files
cp optimize_lightbox_performance.py /home/pi/LightBox2.0/
cp test_optimizations.py /home/pi/LightBox2.0/
cp settings_optimized.json /home/pi/LightBox2.0/config/

# Apply optimized config
cp /home/pi/LightBox2.0/config/settings_optimized.json /home/pi/LightBox2.0/config/settings.json

# Run optimization script
cd /home/pi/LightBox2.0
python3 optimize_lightbox_performance.py

echo "✅ Optimizations installed!"
echo ""
echo "🎮 Next steps:"
echo "1. Restart LightBox: sudo systemctl restart lightbox"
echo "2. Test performance: python3 test_optimizations.py"
echo "3. Check web interface at: http://$(hostname -I | awk '{print $1}'):8888"
echo ""
echo "🎉 Your animations should now be smooth!"
EOF

chmod +x install_on_pi.sh

# Create README for USB deployment
cat > README_USB_DEPLOY.txt << 'EOF'
LightBox Anti-Jitter Optimization Package
=========================================

This package contains fixes for your jittery animation problems.

DEPLOYMENT STEPS:

1. Copy this entire "lightbox_optimizations" folder to a USB drive

2. On your Raspberry Pi:
   - Insert the USB drive
   - Mount it: sudo mount /dev/sda1 /mnt (adjust device as needed)
   - Copy files: cp -r /mnt/lightbox_optimizations ~/
   - Run installer: cd ~/lightbox_optimizations && chmod +x install_on_pi.sh && ./install_on_pi.sh

3. Restart your LightBox service:
   sudo systemctl restart lightbox

WHAT GETS FIXED:
- PWM bits: 11 → 8 (better refresh rate)  
- GPIO slowdown: 4 → 2 (faster updates)
- Hardware PWM: enabled (smoother rendering)
- Double buffering: implemented
- CPU isolation: configured

Your animations should be much smoother after this!
EOF

cd ..
echo ""
echo "✅ USB deployment package created in: lightbox_optimizations/"
echo ""
echo "📋 Instructions:"
echo "1. Copy the 'lightbox_optimizations/' folder to a USB drive"
echo "2. Insert USB into your Pi"
echo "3. Run the install_on_pi.sh script on your Pi"
echo ""
echo "Or try finding your Pi's new IP address:"
echo "- Check your router's admin page"
echo "- Look for 'lightbox' or 'raspberry' devices"
echo "- Try common addresses like 192.168.1.x or 192.168.0.x" 