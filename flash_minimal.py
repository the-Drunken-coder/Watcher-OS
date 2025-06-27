import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from textwrap import dedent

# ---------------------------------------------------------------------------
# Helper utils
# ---------------------------------------------------------------------------

def run(cmd: list[str]):
    print("[RUN]", " ".join(cmd))
    subprocess.check_call(cmd)


def wait_for_boot_drive(timeout=120) -> Path:
    """Wait until a drive containing config.txt appears and return its path."""
    print("Insert (or re-insert) the just-flashed SD card now …")
    t0 = time.time()
    while time.time() - t0 < timeout:
        for p in Path("/mnt").rglob("config.txt"):
            # unlikely on Windows; we fallback later
            return p.parent
        # Windows: enumerate drives like X:\config.txt
        if os.name == "nt":
            import string
            available = [f"{d}:\\" for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]
            for root in available:
                if Path(root, "config.txt").exists():
                    return Path(root)
        time.sleep(2)
    print("Timeout waiting for SD card boot partition.")
    sys.exit(1)


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
    parser = argparse.ArgumentParser(description="Flash Pi OS Lite with Watcher auto-installer.")
    parser.add_argument("--device", help="Target device node (e.g. /dev/sdX or \\?\PhysicalDrive2) for rpi-imager --cli")
    parser.add_argument("--skip-flash", action="store_true", help="Assume SD already flashed; just add installer")
    args = parser.parse_args()

    # Step 1: flash vanilla Pi OS Lite if not skipped
    if not args.skip_flash:
        if not args.device:
            print("--device is required unless --skip-flash is specified")
            sys.exit(1)
        
        # Use a recent stable lite image URL
        image_url = "https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64-lite.img.xz"
        print("Downloading image:", image_url)
        tmpdir = tempfile.gettempdir()
        image_path = Path(tmpdir) / Path(image_url).name
        
        if not image_path.exists():
            print("Downloading Raspberry Pi OS Lite...")
            if os.name == "nt":
                # Use PowerShell on Windows
                run(["powershell", "-Command", f"Invoke-WebRequest -Uri '{image_url}' -OutFile '{image_path}'"])
            else:
                run(["curl", "-L", "-o", str(image_path), image_url])
        else:
            print("Image already downloaded at", image_path)
        
        # Run rpi-imager CLI
        rpi_imager = "rpi-imager"
        if os.name == "nt":
            default_path = Path("C:/Program Files/Raspberry Pi Imager/rpi-imager.exe")
            if default_path.exists():
                rpi_imager = str(default_path)
        
        print("Flashing image to SD card...")
        print("NOTE: You may need to run this as Administrator on Windows")
        run([rpi_imager, "--cli", "--disable-verify", "--enable-writing-system-drives", str(image_path), args.device])

    # Step 2: wait for boot partition mount
    boot_path = wait_for_boot_drive()
    print("Boot partition located at", boot_path)

    # Step 3: add our installer scripts
    make_install_script(boot_path)
    make_firstrun_script(boot_path)

    # Step 4: enable SSH by default
    (boot_path / "ssh").touch(exist_ok=True)

    print("\n✅ SD card prepared!")
    print("🔸 Insert into Pi 5 and power on")
    print("🔸 First boot will download and install Watcher from GitHub")
    print("🔸 Takes ~5-10 minutes depending on internet speed")
    print("🔸 Pi will reboot automatically when done")
    print("🔸 SSH is enabled (default pi/raspberry)")


if __name__ == "__main__":
    main() 