#!/bin/bash
#
# Watcher OS - Master Installation Script
#
# This script installs the complete Watcher OS on a Raspberry Pi
# running a fresh Raspberry Pi OS Lite (64-bit).
#
# Usage:
# curl -sL https://raw.githubusercontent.com/the-Drunken-coder/Watcher-OS/main/install.sh | sudo bash
#

set -e

# --- Colors for logging ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[0;33m'
C_BLUE='\033[0;34m'

# --- Logging functions ---
log() {
    echo -e "${C_BLUE}[INFO]${C_RESET} $1"
}

log_good() {
    echo -e "${C_GREEN}[SUCCESS]${C_RESET} $1"
}

log_warn() {
    echo -e "${C_YELLOW}[WARNING]${C_RESET} $1"
}

log_error() {
    echo -e "${C_RED}[ERROR]${C_RESET} $1" >&2
}

# --- Main installation logic ---
main() {
    log "Starting Watcher OS Installation..."

    # --- Pre-flight checks ---
    log "Performing pre-flight checks..."
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root. Please use 'sudo'."
        exit 1
    fi

    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_error "No internet connection detected. Please connect to the internet."
        exit 1
    fi
    log_good "Pre-flight checks passed."

    # --- System Update and Dependency Installation ---
    log "Updating system packages and installing dependencies..."
    apt-get update -y
    apt-get install -y git python3-pip python3-venv curl libatlas-base-dev unzip libcap-dev
    log_good "System dependencies installed."

    # --- Clone Repository ---
    log "Cloning Watcher OS repository from GitHub to /opt/watcher-os..."
    rm -rf /opt/watcher-os
    git clone https://github.com/the-Drunken-coder/Watcher-OS.git /opt/watcher-os
    cd /opt/watcher-os
    log_good "Repository cloned."

    # --- Python Virtual Environment Setup ---
    log "Setting up Python virtual environment in /opt/watcher-os/venv..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install . # Install the watcher package itself
    deactivate
    log_good "Python environment created and dependencies installed."

    # --- Download AI Model ---
    log "Downloading TensorFlow Lite model..."
    mkdir -p /opt/watcher-os/models
    curl -sL -o /tmp/model.zip "https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
    unzip -j /tmp/model.zip detect.tflite -d /opt/watcher-os/models/
    rm -f /tmp/model.zip
    log_good "AI model downloaded."

    # --- Systemd Service Installation ---
    log "Installing systemd service for Watcher..."
    cat >/etc/systemd/system/watcher.service <<'EOF'
[Unit]
Description=Watcher OS - Object Detection and Geolocation Service
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/watcher-os
ExecStart=/opt/watcher-os/venv/bin/python -m watcher
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable watcher.service
    log_good "Systemd service 'watcher.service' installed and enabled."

    # --- Hardware Configuration (UART) ---
    log "Configuring hardware interfaces (UART)..."
    if ! grep -q "^enable_uart=1" /boot/config.txt; then
        echo "" >> /boot/config.txt
        echo "# Enable UART for Watcher OS" >> /boot/config.txt
        echo "enable_uart=1" >> /boot/config.txt
        log_good "UART has been enabled in /boot/config.txt."
        log_warn "A reboot is required for this change to take effect."
    else
        log_good "UART is already enabled."
    fi

    # --- Final Steps ---
    echo
    log_good "Watcher OS Installation is Complete!"
    log "The 'watcher' service is enabled and will start on the next boot."
    log "To start it now, run: ${C_YELLOW}sudo systemctl start watcher${C_RESET}"
    log "To see its logs, run: ${C_YELLOW}sudo journalctl -u watcher -f${C_RESET}"
    echo
    log "A reboot is recommended to apply all changes."
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Rebooting..."
        reboot
    else
        log "Please reboot the system later to finalize the installation."
    fi
}

# --- Run the main function ---
main 