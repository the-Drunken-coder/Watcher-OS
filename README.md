# Watcher OS

Watcher OS is a Raspberry Pi-based system for object detection and real-world geolocation. It uses a camera to detect objects and communicates with a control computer for positioning data.

## Features

-   **Object Detection**: Detects people, cars, and dogs using a TensorFlow Lite model.
-   **Geolocation**: Calculates the real-world coordinates of detected objects.
-   **Serial Communication**: Communicates with a control computer (like a Pi Zero) over UART.
-   **Headless Operation**: Designed to run automatically as a systemd service.

---

## Installation

The installation process is now simple and reliable. It requires you to flash a standard Raspberry Pi OS image and then run a single command.

### Step 1: Flash Raspberry Pi OS

1.  Download and install the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2.  Choose the following options in the imager:
    -   **Raspberry Pi Device**: Raspberry Pi 5
    -   **Operating System**: Raspberry Pi OS (Other) -> **Raspberry Pi OS Lite (64-bit)**
    -   **Storage**: Your SD card.
3.  **Before writing**, click the **Edit settings** button (the gear icon):
    -   Check **Set hostname** and leave it as `raspberrypi.local`.
    -   Check **Enable SSH** and select **Use password authentication**.
    -   Check **Set username and password** and enter a username and password you will remember (e.g., user: `pi`, pass: `raspberry`).
    -   Check **Configure wireless LAN** and enter your Wi-Fi network's SSID and password.
    -   **Save** your settings.
4.  Click **Write** to flash the SD card.

### Step 2: Boot and Find IP Address

1.  Safely eject the SD card and insert it into your Raspberry Pi 5.
2.  Power on the Pi and wait a minute or two for it to boot and connect to your network.
3.  Find your Pi's IP address. You can often find it by:
    -   Checking your router's "Connected Devices" page for `raspberrypi`.
    -   Using a network scanning tool like "Advanced IP Scanner" on Windows or `nmap` on Linux/macOS.
    -   Pinging the hostname: `ping raspberrypi.local`

### Step 3: Run the Installer

1.  Once you have the IP address, connect to your Pi using SSH from your computer's terminal:
    ```bash
    ssh pi@<your-pi-ip-address>
    ```
2.  You will be prompted for the password you set in the imager.
3.  Once you are logged in, run the following command. This will download the master installation script from GitHub and execute it as the root user:
    ```bash
    curl -sL https://raw.githubusercontent.com/the-Drunken-coder/Watcher-OS/main/install.sh | sudo bash
    ```
4.  The script will handle everything: updating the system, installing dependencies, cloning the repository, setting up the Python environment, and enabling the service.
5.  When it's finished, it will ask if you want to reboot. It's recommended to do so.

That's it! After the reboot, the Watcher OS service will be running automatically.

---

## Verifying the Installation

After the reboot, you can SSH back into the Pi and check the status of the service:

```bash
# Check if the service is active and running
sudo systemctl status watcher

# View the live logs from the service
sudo journalctl -u watcher -f
```

The system is installed in `/opt/watcher-os`. You can view the code and configuration there.

## 🎯 What it does

- **Detects objects** (people, cars, dogs) using TensorFlow Lite
- **Calculates real-world coordinates** using camera bearing/elevation + GPS
- **Communicates with control systems** via serial/UART
- **Runs autonomously** on Raspberry Pi 5

## 🚀 Quick Start

### Easy 2-step install

1. **Flash Raspberry Pi OS Lite (64-bit)** to SD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. **Add Watcher installer:**
   ```bash
   python install_to_sd.py
   ```
3. **Insert SD card in Pi 5 and power on**
4. **Wait 5-10 minutes** - Watcher auto-installs from GitHub and reboots
5. **Done!** Watcher service starts automatically

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