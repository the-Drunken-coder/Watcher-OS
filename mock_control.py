import argparse
import json
import logging
import time

import serial

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_control")

def main(device: str, baud: int, freq: float):
    """
    Simulates a flight controller by sending mock ownship status messages
    over a serial port to the Watcher OS device.
    """
    logger.info(f"Starting mock controller on {device} at {baud} baud.")
    logger.info(f"Sending status messages at {freq} Hz.")

    try:
        ser = serial.Serial(device, baudrate=baud, timeout=1)
    except serial.SerialException as e:
        logger.error(f"Failed to open serial port {device}: {e}")
        return

    # Mock ownship state (e.g., somewhere in California)
    ownship_state = {
        "lat": 37.7749,
        "lon": -122.4194,
        "alt": 100.0,  # meters MSL
        "heading": 90.0, # degrees
        "pitch": 0.0,
        "roll": 0.0,
    }

    try:
        while True:
            # Send ownship state
            message = {"k": "S", "p": ownship_state}
            ser.write((json.dumps(message) + "\n").encode())
            logger.info(f"Sent: {message}")

            # Listen for incoming target messages
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if line:
                    try:
                        received_message = json.loads(line)
                        logger.info(f"Received: {received_message}")
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON message: {line}")
            
            time.sleep(1 / freq)

    except KeyboardInterrupt:
        logger.info("Shutting down mock controller.")
    finally:
        ser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mock Flight Controller for Watcher OS"
    )
    parser.add_argument(
        "--device", default="COM3", help="Serial device name (e.g., COM3, /dev/ttyUSB0)"
    )
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--freq", type=float, default=1.0, help="Message frequency in Hz")
    args = parser.parse_args()

    main(args.device, args.baud, args.freq) 