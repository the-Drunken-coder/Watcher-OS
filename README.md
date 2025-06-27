# Watcher OS

A Raspberry Pi-based object detection and geolocation system for autonomous surveillance.

## 🎯 What it does

- **Detects objects** (people, cars, dogs) using TensorFlow Lite
- **Calculates real-world coordinates** using camera bearing/elevation + GPS
- **Communicates with control systems** via serial/UART
- **Runs autonomously** on Raspberry Pi 5

## 🚀 Quick Start

### Auto-install on fresh Pi OS Lite

1. Flash **Raspberry Pi OS Lite (64-bit)** to SD card
2. Run our installer script:

```bash
# On Windows (as Administrator)
python flash_minimal.py --device "\\?\PhysicalDrive1"

# On Linux/macOS  
python flash_minimal.py --device /dev/sdX
```

3. Insert SD card in Pi 5 and power on
4. Wait 5-10 minutes for auto-installation from GitHub
5. Done! Watcher service starts automatically

### Manual install

```bash
git clone https://github.com/the-Drunken-coder/Watcher-OS.git
cd Watcher-OS
sudo bash install_watcher.sh
```

## 🔧 Hardware Setup

- **Raspberry Pi 5** (main processing)
- **Pi Camera Module** (object detection)
- **Raspberry Pi Zero 2 W** (GPS/control - optional)
- **USB-serial adapter** (for Pi-to-Pi communication)

## 📡 System Architecture

```
┌─────────────────┐    Serial/UART    ┌─────────────────┐
│   Pi Zero 2W    │◄─────────────────►│   Pi 5 (Main)   │
│  (GPS/Control)  │                   │   (Watcher)     │
│                 │                   │                 │
│ • Position data │                   │ • Camera input  │
│ • Altitude      │                   │ • AI detection  │
│ • System state  │                   │ • Geolocation   │
└─────────────────┘                   └─────────────────┘
```

## 🎛️ Configuration

- Edit `watcher/main.py` for camera FOV and detection settings
- Modify serial device in `watcher/serial_comm.py` 
- Adjust detection thresholds in `watcher/detector.py`

## 🔍 Supported Objects

- **Person** (COCO class 0)
- **Car** (COCO class 2) 
- **Truck** (COCO class 7)
- **Dog** (COCO class 16) - also detects coyotes

## 📋 Requirements

See `requirements.txt` for Python dependencies. Key libraries:
- `picamera2` - Camera interface
- `opencv-python-headless` - Image processing  
- `tflite-runtime` - AI inference
- `pyserial` - Serial communication
- `ags-geolocation` - Coordinate calculation

## 🛠️ Development

```bash
# Install in development mode
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .

# Test without hardware
python mock_control.py  # simulates Pi Zero 2W
python -m watcher       # runs detection (needs camera)
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Pull requests welcome! Please ensure code follows existing style and include tests for new features. 