#!/bin/bash
# Raspberry Pi System Optimization for HUB75 LED Matrix
# Implements all optimizations from LighboxEnhancementsStructure.txt

set -e

echo "🔧 Optimizing Raspberry Pi system for HUB75 LED Matrix..."
echo "📋 Based on LighboxEnhancementsStructure.txt requirements"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

echo "1️⃣ CPU Isolation Setup"
echo "========================"

# Add CPU isolation to cmdline.txt
CMDLINE_FILE="/boot/cmdline.txt"
if [ -f "$CMDLINE_FILE" ]; then
    echo "📝 Backing up original cmdline.txt..."
    cp "$CMDLINE_FILE" "${CMDLINE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Check if isolcpus is already set
    if grep -q "isolcpus=" "$CMDLINE_FILE"; then
        echo "⚠️  isolcpus already configured in cmdline.txt"
    else
        echo "➕ Adding CPU isolation (isolcpus=3) to cmdline.txt..."
        sed -i '$ s/$/ isolcpus=3/' "$CMDLINE_FILE"
        echo "✅ CPU core 3 will be isolated for LED matrix refresh"
    fi
else
    echo "❌ /boot/cmdline.txt not found"
fi

echo ""
echo "2️⃣ Audio System Optimization"
echo "============================="

# Disable built-in audio (conflicts with HUB75)
echo "🔇 Disabling Pi built-in audio (conflicts with HUB75)..."

# Add audio disable to config.txt
CONFIG_FILE="/boot/config.txt"
if [ -f "$CONFIG_FILE" ]; then
    echo "📝 Backing up original config.txt..."
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Disable audio
    if grep -q "dtparam=audio=off" "$CONFIG_FILE"; then
        echo "⚠️  Audio already disabled in config.txt"
    else
        echo "dtparam=audio=off" >> "$CONFIG_FILE"
        echo "✅ Built-in audio disabled"
    fi
    
    # Set GPU memory split
    if grep -q "gpu_mem=" "$CONFIG_FILE"; then
        echo "⚠️  GPU memory already configured"
    else
        echo "gpu_mem=16" >> "$CONFIG_FILE"
        echo "✅ GPU memory set to 16MB (minimal for headless)"
    fi
else
    echo "❌ /boot/config.txt not found"
fi

# Blacklist audio modules
BLACKLIST_FILE="/etc/modprobe.d/blacklist-rgb-matrix.conf"
echo "📝 Creating audio module blacklist..."
cat > "$BLACKLIST_FILE" << EOF
# Blacklist audio modules that conflict with HUB75 LED matrix
blacklist snd_bcm2835
blacklist snd_pcm
blacklist snd_timer
blacklist snd
EOF
echo "✅ Audio modules blacklisted"

echo ""
echo "3️⃣ Performance Optimizations"
echo "============================="

# Disable unnecessary services
echo "🛑 Disabling unnecessary services..."
SERVICES_TO_DISABLE=(
    "bluetooth"
    "hciuart" 
    "cups"
    "cups-browsed"
    "avahi-daemon"
    "triggerhappy"
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-enabled "$service" &>/dev/null; then
        systemctl disable "$service"
        echo "✅ Disabled $service"
    else
        echo "⚠️  $service already disabled or not found"
    fi
done

echo ""
echo "4️⃣ Hardware PWM Configuration"
echo "============================="

# Check for hardware PWM jumper
echo "⚡ Hardware PWM Status:"
echo "   - For best quality, solder GPIO4 to GPIO18 on HAT/Bonnet"
echo "   - This enables hardware PWM for stable colors"
echo "   - Without this mod, system will use software PWM"

# Create systemd service for LightBox
echo ""
echo "5️⃣ LightBox Service Setup"
echo "========================="

SERVICE_FILE="/etc/systemd/system/lightbox.service"
echo "📝 Creating LightBox systemd service..."

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=LightBox HUB75 LED Matrix Controller
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/joshuafield/LightBox2.0
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/joshuafield/LightBox2.0
StandardOutput=journal
StandardError=journal

# Performance settings
Nice=-10
IOSchedulingClass=1
IOSchedulingPriority=4

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ LightBox service created"

echo ""
echo "6️⃣ Network Optimizations"
echo "========================"

# Optimize network settings for web interface
echo "🌐 Optimizing network settings..."
cat > "/etc/sysctl.d/99-lightbox.conf" << EOF
# LightBox network optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
EOF

echo "✅ Network optimizations applied"

echo ""
echo "🎯 OPTIMIZATION COMPLETE!"
echo "========================="
echo ""
echo "📋 Applied optimizations:"
echo "   ✅ CPU core 3 isolated for LED matrix refresh"
echo "   ✅ Built-in audio disabled (prevents conflicts)"
echo "   ✅ GPU memory minimized (16MB)"
echo "   ✅ Unnecessary services disabled"
echo "   ✅ LightBox systemd service created"
echo "   ✅ Network performance optimized"
echo ""
echo "⚠️  REBOOT REQUIRED for all changes to take effect!"
echo ""
echo "🚀 After reboot, you can:"
echo "   • Start: sudo systemctl start lightbox"
echo "   • Enable auto-start: sudo systemctl enable lightbox"
echo "   • Check status: sudo systemctl status lightbox"
echo ""
echo "💡 For hardware PWM (best quality):"
echo "   • Solder GPIO4 to GPIO18 on your HAT/Bonnet"
echo "   • This eliminates display flicker"
echo ""
read -p "🔄 Reboot now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Rebooting system..."
    reboot
else
    echo "⚠️  Remember to reboot manually when ready!"
fi 