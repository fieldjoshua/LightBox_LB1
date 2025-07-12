# LightBox Hardware Monitor Agent

## Overview

The LightBox Hardware Monitor Agent is a background service that continuously monitors hardware performance and helps diagnose issues with the LED matrix. It's designed to run alongside the main LightBox application on Raspberry Pi devices.

## Features

- **Real-time Monitoring**: Continuously tracks CPU usage, memory usage, and temperature
- **Issue Detection**: Automatically identifies potential hardware issues
- **LED Matrix Diagnostics**: Runs specialized tests for HUB75 matrix hardware
- **Performance History**: Maintains a history of system performance metrics
- **Detailed Diagnostics**: Provides comprehensive system information for troubleshooting

## How It Works

The agent works by:

1. Collecting system metrics at regular intervals (CPU, memory, temperature)
2. Analyzing the metrics for potential issues
3. Detecting and diagnosing LED matrix hardware problems
4. Logging warnings and errors for later review
5. Providing diagnostic information on demand

## Usage

To use the Hardware Monitor Agent:

```bash
sudo python3 hardware_monitor_agent.py
```

The agent will start monitoring in the background and log any issues to `hardware_monitor.log`.

## Monitored Issues

The agent monitors for several types of issues:

### System Issues
- **High CPU Usage**: When CPU usage exceeds 90%
- **High Memory Usage**: When memory usage exceeds 90%
- **High Temperature**: Warning at 70°C, critical at 80°C

### LED Matrix Issues
- **GPIO Conflicts**: Detects conflicts with other hardware using the same GPIO pins
- **Power Supply Issues**: Identifies inadequate power supply for the LED matrix
- **Connection Problems**: Detects loose or faulty connections

## Example Output

```
2023-06-15 14:23:45 - HardwareMonitor - INFO - Starting LightBox Hardware Monitor Agent
2023-06-15 14:23:45 - HardwareMonitor - INFO - Detecting LED matrix hardware...
2023-06-15 14:23:45 - HardwareMonitor - INFO - Detected HUB75 matrix with adafruit-hat
2023-06-15 14:23:45 - HardwareMonitor - INFO - Running initial matrix diagnostics
2023-06-15 14:23:45 - HardwareMonitor - INFO - No matrix issues detected
2023-06-15 14:23:50 - HardwareMonitor - WARNING - Issue detected: CPU temperature is high: 72.5°C
2023-06-15 14:24:20 - HardwareMonitor - WARNING - Issue detected: CPU usage is high: 95.2%
```

## Diagnostic Information

The agent can provide detailed diagnostic information including:

- CPU usage, cores, and frequency
- Memory usage and availability
- Current and average temperature
- Disk usage and free space
- System uptime
- Recent issues
- LED matrix configuration

## Requirements

- Python 3.6+
- psutil library (`pip install psutil`)
- Root/sudo access (for hardware access)
- Raspberry Pi running LightBox

## Integration with LightBox

This agent is designed to work alongside the main LightBox application, providing valuable diagnostic information without interfering with normal operation. It can help identify and resolve issues that might affect LED matrix performance. 