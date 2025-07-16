#!/bin/bash
# Deploy optimizations via Tailscale once SSH is working

PI_IP="100.114.157.110"

echo "🚀 Deploying optimizations via Tailscale to $PI_IP..."

# Test connection first
ssh pi@$PI_IP "echo 'Connection successful!'" || {
    echo "❌ SSH connection failed. Make sure SSH keys are set up."
    echo "Run this on your Pi first:"
    echo "echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEk3uOA/YIn/OwRyvSMejx7N4lVHMv+HOARPriHspTyV pi@raspberrypi' >> ~/.ssh/authorized_keys"
    exit 1
}

# Backup current config
echo "📋 Creating backup..."
ssh pi@$PI_IP "cd /home/pi/LightBox2.0 && cp config/settings.json config/settings_backup_\$(date +%Y%m%d_%H%M%S).json" || true

# Deploy files
echo "📦 Copying optimization files..."
scp optimize_lightbox_performance.py pi@$PI_IP:/home/pi/LightBox2.0/
scp config/settings_optimized.json pi@$PI_IP:/home/pi/LightBox2.0/config/
scp test_optimizations.py pi@$PI_IP:/home/pi/LightBox2.0/

# Apply optimizations
echo "⚙️ Applying optimizations..."
ssh pi@$PI_IP "cd /home/pi/LightBox2.0 && cp config/settings_optimized.json config/settings.json && python3 optimize_lightbox_performance.py"

# Test optimizations
echo "🧪 Testing optimizations..."
ssh pi@$PI_IP "cd /home/pi/LightBox2.0 && python3 test_optimizations.py"

echo "✅ Deployment complete!"
echo ""
echo "🎮 Next steps:"
echo "1. Restart LightBox: ssh pi@$PI_IP 'sudo systemctl restart lightbox'"
echo "2. Access web interface: http://$PI_IP:8888"
echo ""
echo "🎉 Your animations should now be smooth!" 