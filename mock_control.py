import random
import time

from watcher.serial_comm import Message, SerialWorker


def main():
    worker = SerialWorker(device="stub")
    worker.start()

    # Static reference point (somewhere NY)
    lat, lon = 40.7128, -74.0060
    alt = 120.0  # metres above sea level

    try:
        while True:
            # Slight jiggle to simulate movement
            lat += (random.random() - 0.5) * 1e-5
            lon += (random.random() - 0.5) * 1e-5
            heading = random.uniform(0, 359)
            pitch = 0.0
            roll = 0.0

            worker.send(
                Message(
                    kind="S",
                    payload={
                        "lat": lat,
                        "lon": lon,
                        "alt": alt,
                        "heading": heading,
                        "pitch": pitch,
                        "roll": roll,
                    },
                )
            )

            # Check for returned targets
            msg = worker.recv_nowait()
            if msg and msg.kind == "T":
                print("[TARGET]", msg.payload)

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping control mock...")
    finally:
        worker.stop()


if __name__ == "__main__":
    main() 