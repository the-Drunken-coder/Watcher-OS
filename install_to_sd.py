import os
import time
from pathlib import Path
from textwrap import dedent

def find_pi_boot_drive():
    """Find the Pi OS boot partition by looking for config.txt."""
    # Windows: check drive letters
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            boot_path = Path(f"{letter}:\\")
            if (boot_path / "config.txt").exists():
                return boot_path
    
    # Linux/macOS: check common mount points
    for mount_point in ["/boot", "/mnt", "/media"]:
        for p in Path(mount_point).rglob("config.txt"):
            return p.parent
    
    return None

def make_install_script(boot_path: Path):
    """Create the GitHub-based installer script."""
    install_script = boot_path / "install_watcher.sh"
    install_script.write_text(
        dedent(
            """#!/bin/bash
            set -e
            echo '[WATCHER INSTALL] Starting installation from GitHub' | systemd-cat -t watcher-install

            # Update system
            apt-get update -y
            apt-get install -y git python3-pip python3-venv curl libatlas-base-dev

            # Clone the repo
            echo '[WATCHER INSTALL] Cloning repository' | systemd-cat -t watcher-install
            rm -rf /opt/watcher-src
            git clone https://github.com/the-Drunken-coder/Watcher-OS.git /opt/watcher-src
            cd /opt/watcher-src

            # Create virtual environment
            echo '[WATCHER INSTALL] Setting up Python environment' | systemd-cat -t watcher-install
            python3 -m venv /opt/watcher
            /opt/watcher/bin/pip install --upgrade pip

            # Install dependencies and watcher package
            /opt/watcher/bin/pip install -r requirements.txt
            /opt/watcher/bin/pip install .

            # Download TFLite model
            echo '[WATCHER INSTALL] Downloading AI model' | systemd-cat -t watcher-install
            mkdir -p /opt/watcher/models
            curl -L -o /tmp/model.zip "https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
            cd /tmp && unzip -j model.zip detect.tflite
            mv detect.tflite /opt/watcher/models/ssd_mobilenet_v2_fpnlite_320x320.tflite
            rm /tmp/model.zip

            # Install systemd service
            echo '[WATCHER INSTALL] Installing service' | systemd-cat -t watcher-install
            cat >/etc/systemd/system/watcher.service <<'EOF'
[Unit]
Description=Watcher object-detection & geolocation
After=network-online.target

[Service]
Type=simple
ExecStart=/opt/watcher/bin/python -m watcher
Restart=always
User=pi
Environment=PYTHONPATH=/opt/watcher-src

[Install]
WantedBy=multi-user.target
EOF

            systemctl enable watcher.service

            # Enable UART for Pi Zero communication
            if ! grep -q '^enable_uart=1' /boot/config.txt; then
              echo 'enable_uart=1' >> /boot/config.txt
            fi

            echo '[WATCHER INSTALL] Installation complete!' | systemd-cat -t watcher-install
            
            # Clean up and reboot
            rm -f /boot/install_watcher.sh
            rm -rf /opt/watcher-src/.git  # Save space
            
            echo '[WATCHER INSTALL] Rebooting...' | systemd-cat -t watcher-install
            reboot
            """
        )
    )
    install_script.chmod(0o755)

def make_firstrun_script(boot_path: Path):
    """Create the first-run script that executes our installer."""
    firstrun = boot_path / "firstrun.sh"
    firstrun.write_text(
        dedent(
            """#!/bin/bash
            # This runs once on first boot
            if [ -f /boot/install_watcher.sh ]; then
                echo 'Running Watcher installer...'
                bash /boot/install_watcher.sh
            fi
            """
        )
    )
    firstrun.chmod(0o755)

def main():
    print("🔍 Looking for Raspberry Pi OS boot partition...")
    
    boot_path = find_pi_boot_drive()
    if not boot_path:
        print("❌ No Pi OS boot partition found!")
        print("   Make sure your SD card with Pi OS Lite is inserted and mounted.")
        return
    
    print(f"✅ Found Pi OS boot partition: {boot_path}")
    
    # Add installer scripts
    print("📝 Adding Watcher installer scripts...")
    make_install_script(boot_path)
    make_firstrun_script(boot_path)
    
    # Enable SSH
    print("🔑 Enabling SSH...")
    (boot_path / "ssh").touch(exist_ok=True)
    
    print("\n🎉 SD card prepared for Watcher OS!")
    print(f"📍 Boot partition: {boot_path}")
    print("📄 Files added:")
    print("   • install_watcher.sh  (downloads & installs from GitHub)")
    print("   • firstrun.sh         (triggers installer on first boot)")
    print("   • ssh                 (enables SSH access)")
    print("\n🚀 Next steps:")
    print("   1. Safely eject SD card")
    print("   2. Insert into Raspberry Pi 5")
    print("   3. Power on and wait 5-10 minutes")
    print("   4. Pi will auto-install Watcher and reboot")
    print("   5. SSH: ssh pi@<pi-ip-address> (default password: raspberry)")

if __name__ == "__main__":
    main() 