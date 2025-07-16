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
