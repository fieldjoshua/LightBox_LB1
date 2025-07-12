# Integrating Background Agents with LightBox

This guide provides instructions for integrating the AI Animation Assistant and Hardware Monitor Agent with your LightBox installation.

## Prerequisites

Before integrating the background agents, make sure you have:

1. A working LightBox installation
2. Python 3.6 or higher
3. Administrative access to your Raspberry Pi
4. Required Python packages:
   - psutil
   - numpy (optional, for advanced animation analysis)

## Installation

### Step 1: Install Dependencies

```bash
# Install required packages
pip3 install psutil numpy
```

### Step 2: Copy Agent Files

Copy the following files to your LightBox installation directory:

- `ai_animation_assistant.py`
- `hardware_monitor_agent.py`

### Step 3: Configure Permissions

Make the scripts executable:

```bash
chmod +x ai_animation_assistant.py
chmod +x hardware_monitor_agent.py
```

## Running the Agents

### AI Animation Assistant

Run the AI Animation Assistant manually:

```bash
python3 ai_animation_assistant.py
```

This will analyze all animations in your `scripts` directory and provide optimization suggestions.

### Hardware Monitor Agent

Run the Hardware Monitor Agent manually:

```bash
sudo python3 hardware_monitor_agent.py
```

This will start monitoring your system's hardware performance and log any issues to `hardware_monitor.log`.

## Setting Up Automatic Startup

### Method 1: Using Systemd

Create systemd service files for automatic startup:

1. Create the AI Animation Assistant service file:

```bash
sudo nano /etc/systemd/system/lightbox-animation-assistant.service
```

Add the following content:

```
[Unit]
Description=LightBox AI Animation Assistant
After=lightbox.service

[Service]
ExecStart=/usr/bin/python3 /path/to/ai_animation_assistant.py
WorkingDirectory=/path/to/lightbox
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

2. Create the Hardware Monitor Agent service file:

```bash
sudo nano /etc/systemd/system/lightbox-hardware-monitor.service
```

Add the following content:

```
[Unit]
Description=LightBox Hardware Monitor Agent
After=lightbox.service

[Service]
ExecStart=/usr/bin/python3 /path/to/hardware_monitor_agent.py
WorkingDirectory=/path/to/lightbox
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

3. Enable and start the services:

```bash
sudo systemctl enable lightbox-animation-assistant.service
sudo systemctl enable lightbox-hardware-monitor.service
sudo systemctl start lightbox-animation-assistant.service
sudo systemctl start lightbox-hardware-monitor.service
```

### Method 2: Using Cron

Alternatively, you can use cron to start the agents at boot:

```bash
sudo crontab -e
```

Add the following lines:

```
@reboot /usr/bin/python3 /path/to/hardware_monitor_agent.py > /path/to/hardware_monitor.log 2>&1
```

And for the regular user:

```bash
crontab -e
```

Add:

```
@reboot /usr/bin/python3 /path/to/ai_animation_assistant.py > /path/to/animation_assistant.log 2>&1
```

## Integration with Web Interface

To integrate the agents with LightBox's web interface:

1. Create an API endpoint in your web application to fetch data from the agents
2. Add a new section to the web interface for displaying agent data
3. Use AJAX to periodically update the display with fresh data

Example Flask API endpoint:

```python
@app.route('/api/agent-data', methods=['GET'])
def get_agent_data():
    # Read the latest data from the agents
    hardware_data = {}
    animation_data = {}
    
    try:
        # Read hardware monitor data
        if os.path.exists('hardware_monitor.log'):
            with open('hardware_monitor.log', 'r') as f:
                # Process log data
                hardware_data = parse_hardware_log(f.readlines())
    except Exception as e:
        hardware_data = {"error": str(e)}
    
    try:
        # Run animation analysis
        animation_analyzer = AnimationAnalyzer()
        animation_data = {
            "animations": {},
            "suggestions": {}
        }
        
        for name in animation_analyzer.animations:
            analysis = animation_analyzer.analyze_animation(name)
            suggestions = animation_analyzer.suggest_optimizations(name)
            animation_data["animations"][name] = analysis
            animation_data["suggestions"][name] = suggestions
    except Exception as e:
        animation_data = {"error": str(e)}
    
    return jsonify({
        "hardware": hardware_data,
        "animations": animation_data
    })
```

## Troubleshooting

### Common Issues

1. **Agents not starting automatically**
   - Check service status: `sudo systemctl status lightbox-hardware-monitor.service`
   - Check log files for errors

2. **Permission errors**
   - Make sure the hardware monitor is running as root
   - Check file permissions on the scripts

3. **High CPU usage**
   - Adjust the check interval in the hardware monitor
   - Limit the number of animations analyzed at once

4. **Missing animation data**
   - Ensure animations have the standard `animate(pixels, config, frame)` function
   - Check the path to the scripts directory

## Advanced Configuration

### Hardware Monitor Configuration

Edit `hardware_monitor_agent.py` to adjust thresholds:

```python
self.temperature_warning = 70  # Celsius
self.temperature_critical = 80  # Celsius
self.cpu_warning = 90  # percent
self.memory_warning = 90  # percent
self.check_interval = 5  # seconds
```

### Animation Assistant Configuration

Edit `ai_animation_assistant.py` to customize analysis parameters:

```python
# Adjust analysis settings
self.complexity_threshold = 100
self.frame_time_warning = 0.01  # seconds
self.pixel_change_threshold = 5  # percent
```

## Next Steps

After integrating the background agents, consider:

1. Creating a unified dashboard for monitoring
2. Implementing automatic optimization of animations
3. Setting up email or push notifications for critical issues
4. Expanding the hardware monitor to check for additional issues
5. Training a custom ML model for animation generation 