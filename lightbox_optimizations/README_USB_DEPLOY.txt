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
