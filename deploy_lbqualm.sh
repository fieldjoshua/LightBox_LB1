#!/bin/bash
# 🌈 LBQualm Deployment Script
# ==========================
# 
# Deploy the ultimate HUB75 LightBox system to Raspberry Pi 3B+
# This script handles everything needed to get LBQualm running
#
# Usage: ./deploy_lbqualm.sh [HOSTNAME]
# Example: ./deploy_lbqualm.sh lightbox.local

set -e  # Exit on any error

# Configuration
PI_USER="joshuafield"
PI_HOST="${1:-lightbox.local}"
PROJECT_NAME="LBQualm"
REMOTE_DIR="/home/$PI_USER/$PROJECT_NAME"
WEB_PORT=5000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo
}

# Check if files exist
check_files() {
    print_header "🔍 CHECKING DEPLOYMENT FILES"
    
    local files=(
        "LBQualm.py"
        "requirements_hub75_optimized.txt"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "Found: $file"
        else
            print_error "Missing: $file"
            exit 1
        fi
    done
}

# Test SSH connection
test_ssh() {
    print_header "🔗 TESTING SSH CONNECTION"
    
    print_status "Testing connection to $PI_USER@$PI_HOST..."
    
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
        print_success "SSH connection established"
    else
        print_error "Cannot connect to $PI_USER@$PI_HOST"
        print_warning "Make sure:"
        echo "  - Pi is powered on and connected to network"
        echo "  - SSH is enabled on the Pi"
        echo "  - Hostname/IP is correct"
        echo "  - SSH keys are set up or password is available"
        exit 1
    fi
}

# Deploy files to Pi
deploy_files() {
    print_header "📦 DEPLOYING FILES TO PI"
    
    print_status "Creating remote directory: $REMOTE_DIR"
    ssh "$PI_USER@$PI_HOST" "mkdir -p $REMOTE_DIR"
    
    print_status "Copying LBQualm files..."
    scp LBQualm.py "$PI_USER@$PI_HOST:$REMOTE_DIR/"
    scp requirements_hub75_optimized.txt "$PI_USER@$PI_HOST:$REMOTE_DIR/"
    
    print_success "Files deployed successfully"
}

# Install dependencies on Pi
install_dependencies() {
    print_header "📚 INSTALLING DEPENDENCIES"
    
    print_status "Updating package lists..."
    ssh "$PI_USER@$PI_HOST" "sudo apt-get update -qq"
    
    print_status "Installing system packages..."
    ssh "$PI_USER@$PI_HOST" "sudo apt-get install -y python3-pip python3-dev python3-venv git"
    
    print_status "Creating Python virtual environment..."
    ssh "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && python3 -m venv lbqualm_env"
    
    print_status "Installing Python packages..."
    ssh "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && source lbqualm_env/bin/activate && pip install -r requirements_hub75_optimized.txt"
    
    print_success "Dependencies installed"
}

# Install RGB Matrix library
install_rgb_matrix() {
    print_header "🌈 INSTALLING RGB MATRIX LIBRARY"
    
    print_status "Checking if RGB Matrix library is already installed..."
    
    if ssh "$PI_USER@$PI_HOST" "python3 -c 'import rgbmatrix' 2>/dev/null"; then
        print_warning "RGB Matrix library already installed, skipping"
        return
    fi
    
    print_status "Installing RGB Matrix library dependencies..."
    ssh "$PI_USER@$PI_HOST" "sudo apt-get install -y build-essential git python3-dev python3-pillow"
    
    print_status "Cloning and building RGB Matrix library..."
    ssh "$PI_USER@$PI_HOST" "
        cd /tmp
        git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
        cd rpi-rgb-led-matrix
        make build-python PYTHON=python3
        sudo make install-python PYTHON=python3
    "
    
    print_status "Testing RGB Matrix library installation..."
    if ssh "$PI_USER@$PI_HOST" "python3 -c 'import rgbmatrix; print(\"RGB Matrix library installed successfully\")'" 2>/dev/null; then
        print_success "RGB Matrix library installed and working"
    else
        print_warning "RGB Matrix library installation may have issues"
        print_warning "LBQualm will run in simulation mode"
    fi
}

# Configure system optimizations
configure_system() {
    print_header "⚙️ CONFIGURING SYSTEM OPTIMIZATIONS"
    
    print_status "Configuring GPU memory split..."
    ssh "$PI_USER@$PI_HOST" "
        sudo sed -i '/^gpu_mem=/d' /boot/config.txt
        echo 'gpu_mem=16' | sudo tee -a /boot/config.txt
    "
    
    print_status "Checking for CPU isolation..."
    if ssh "$PI_USER@$PI_HOST" "grep -q 'isolcpus=' /boot/cmdline.txt"; then
        print_success "CPU isolation already configured"
    else
        print_status "Configuring CPU isolation for core 3..."
        ssh "$PI_USER@$PI_HOST" "
            sudo cp /boot/cmdline.txt /boot/cmdline.txt.backup
            sudo sed -i 's/$/ isolcpus=3/' /boot/cmdline.txt
        "
        print_success "CPU isolation configured (will take effect after reboot)"
    fi
    
    print_status "Disabling unnecessary services..."
    ssh "$PI_USER@$PI_HOST" "
        sudo systemctl disable bluetooth.service || true
        sudo systemctl disable hciuart.service || true
        sudo systemctl disable avahi-daemon.service || true
    "
    
    print_success "System optimizations configured"
}

# Create systemd service
create_service() {
    print_header "🚀 CREATING SYSTEMD SERVICE"
    
    print_status "Creating LBQualm systemd service..."
    
    ssh "$PI_USER@$PI_HOST" "cat > /tmp/lbqualm.service << 'EOF'
[Unit]
Description=LBQualm - Ultimate HUB75 LightBox System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$PI_USER
WorkingDirectory=$REMOTE_DIR
Environment=PATH=$REMOTE_DIR/lbqualm_env/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$REMOTE_DIR/lbqualm_env/bin/python $REMOTE_DIR/LBQualm.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"
    
    ssh "$PI_USER@$PI_HOST" "
        sudo mv /tmp/lbqualm.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable lbqualm.service
    "
    
    print_success "Systemd service created and enabled"
}

# Test LBQualm installation
test_installation() {
    print_header "🧪 TESTING LBQUALM INSTALLATION"
    
    print_status "Testing LBQualm script syntax..."
    if ssh "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && source lbqualm_env/bin/activate && python3 -m py_compile LBQualm.py"; then
        print_success "LBQualm script syntax is valid"
    else
        print_error "LBQualm script has syntax errors"
        exit 1
    fi
    
    print_status "Testing import dependencies..."
    if ssh "$PI_USER@$PI_HOST" "cd $REMOTE_DIR && source lbqualm_env/bin/activate && python3 -c 'import flask, flask_cors; print(\"Dependencies OK\")'"; then
        print_success "All dependencies import successfully"
    else
        print_error "Dependency import failed"
        exit 1
    fi
    
    print_success "Installation test completed"
}

# Start LBQualm service
start_service() {
    print_header "▶️ STARTING LBQUALM SERVICE"
    
    print_status "Starting LBQualm service..."
    ssh "$PI_USER@$PI_HOST" "sudo systemctl start lbqualm.service"
    
    sleep 3
    
    print_status "Checking service status..."
    if ssh "$PI_USER@$PI_HOST" "sudo systemctl is-active lbqualm.service" | grep -q "active"; then
        print_success "LBQualm service is running"
        
        print_status "Checking web interface..."
        sleep 2
        
        if ssh "$PI_USER@$PI_HOST" "curl -s http://localhost:$WEB_PORT/api/health" > /dev/null 2>&1; then
            print_success "Web interface is responding"
        else
            print_warning "Web interface may not be ready yet"
        fi
    else
        print_warning "Service may not be running properly"
        print_status "Checking service logs..."
        ssh "$PI_USER@$PI_HOST" "sudo journalctl -u lbqualm.service --no-pager -n 10"
    fi
}

# Get Pi IP for web access
get_pi_ip() {
    print_header "🌐 WEB ACCESS INFORMATION"
    
    local pi_ip
    pi_ip=$(ssh "$PI_USER@$PI_HOST" "hostname -I | cut -d' ' -f1" 2>/dev/null || echo "unknown")
    
    print_success "🌈 LBQualm Deployment Completed!"
    echo
    echo -e "${CYAN}Web Interface Access:${NC}"
    echo "  🔗 http://$pi_ip:$WEB_PORT"
    echo "  🔗 http://$PI_HOST:$WEB_PORT"
    echo
    echo -e "${CYAN}Service Management:${NC}"
    echo "  ▶️  Start:   ssh $PI_USER@$PI_HOST 'sudo systemctl start lbqualm.service'"
    echo "  ⏹️  Stop:    ssh $PI_USER@$PI_HOST 'sudo systemctl stop lbqualm.service'"
    echo "  🔄 Restart: ssh $PI_USER@$PI_HOST 'sudo systemctl restart lbqualm.service'"
    echo "  📊 Status:  ssh $PI_USER@$PI_HOST 'sudo systemctl status lbqualm.service'"
    echo "  📝 Logs:    ssh $PI_USER@$PI_HOST 'sudo journalctl -u lbqualm.service -f'"
    echo
    echo -e "${CYAN}Hardware Notes:${NC}"
    echo "  ⚡ For best performance, solder GPIO4-GPIO18 jumper on RGB HAT"
    echo "  🔄 Reboot Pi to activate CPU isolation: ssh $PI_USER@$PI_HOST 'sudo reboot'"
    echo "  🌡️  Monitor temperature and performance via web interface"
    echo
}

# Print usage information
print_usage() {
    echo "🌈 LBQualm Deployment Script"
    echo
    echo "Usage: $0 [HOSTNAME]"
    echo
    echo "Examples:"
    echo "  $0                      # Deploy to lightbox.local (default)"
    echo "  $0 lightbox.local       # Deploy to specific hostname"
    echo "  $0 192.168.1.100        # Deploy to specific IP"
    echo
    echo "Requirements:"
    echo "  - SSH access to target Pi"
    echo "  - Pi running Raspberry Pi OS"
    echo "  - LBQualm.py and requirements_hub75_optimized.txt in current directory"
    echo
}

# Main deployment function
main() {
    # Check for help flag
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        print_usage
        exit 0
    fi
    
    print_header "🌈 LBQUALM DEPLOYMENT TO RASPBERRY PI 3B+"
    echo -e "${CYAN}Target: $PI_USER@$PI_HOST${NC}"
    echo -e "${CYAN}Remote Directory: $REMOTE_DIR${NC}"
    echo
    
    # Deployment steps
    check_files
    test_ssh
    deploy_files
    install_dependencies
    install_rgb_matrix
    configure_system
    create_service
    test_installation
    start_service
    get_pi_ip
    
    print_header "🎉 DEPLOYMENT COMPLETE!"
}

# Run main function
main "$@" 