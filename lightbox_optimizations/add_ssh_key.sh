#!/bin/bash
# SSH Key Setup Script for Pi
# Transfer this file to your Pi and run it

echo "🔑 Adding SSH key for Mac access..."

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh

# Add the SSH key
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEk3uOA/YIn/OwRyvSMejx7N4lVHMv+HOARPriHspTyV pi@raspberrypi" >> ~/.ssh/authorized_keys

# Set proper permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

echo "✅ SSH key added successfully!"
echo "You can now SSH from your Mac without passwords." 