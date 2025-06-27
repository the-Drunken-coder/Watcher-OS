import logging
import signal
import time
from math import radians, tan, atan

import cv2

from .camera import open_camera
from .detector import Detector
from .serial_comm import Message, SerialWorker
from .geolocate import GeoLocator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watcher")


class WatcherApp:
    def __init__(self):
        self.serial = SerialWorker()
        self.serial.start()
        self.detector = Detector()
        self.geo = GeoLocator()
        self._running = True

    # ------------------------------------------------------------------
    def run(self):
        def _sigint(_sig, _frame):
            self._running = False

        signal.signal(signal.SIGINT, _sigint)

        with open_camera() as cam:
            for frame in cam.frames():
                # Check for control messages (ownship state)
                msg = self.serial.recv_nowait()
                if msg and msg.kind == "S":
                    own = msg.payload  # expects lat, lon, alt, heading, pitch, roll
                else:
                    own = None

                detections = self.detector.detect(frame)
                if detections and own:
                    # For simplicity, use center of first bbox
                    xmin, ymin, xmax, ymax = detections[0].bbox
                    cx = (xmin + xmax) / 2
                    cy = (ymin + ymax) / 2

                    bearing, elevation = self._pixel_to_angles(cx, cy, frame.shape)
                    tgt_lat, tgt_lon = self.geo.locate_target(
                        own_lat=own["lat"],
                        own_lon=own["lon"],
                        own_alt_msl=own["alt"],
                        bearing_deg=bearing,
                        elevation_deg=elevation,
                    )
                    self.serial.send(
                        Message(kind="T", payload={
                            "lat": tgt_lat,
                            "lon": tgt_lon,
                            "cls": detections[0].class_id,
                            "conf": detections[0].score,
                            "ts": time.time(),
                        })
                    )

                # Display for debugging (disabled in headless)
                # cv2.imshow("watcher", frame)
                # cv2.waitKey(1)

                if not self._running:
                    break

        logger.info("Shutting down ...")
        self.serial.stop()

    # ------------------------------------------------------------------
    @staticmethod
    def _pixel_to_angles(px: float, py: float, shape):
        """Convert pixel location to bearing/elevation offset.

        Placeholder: assumes camera FOV 62.2° horiz, 48.8° vert and camera aligned with heading+0 pitch.
        """
        h, w, _ = shape
        # Camera horizontal/vertical Field-of-View in degrees (Sony IMX477 std lens)
        fov_h = 62.2
        fov_v = 48.8

        # Convert pixel offset to angle via simple pinhole approximation
        dx = (px - w / 2) / (w / 2)
        dy = (py - h / 2) / (h / 2)

        bearing_off_deg = dx * fov_h / 2.0
        elev_off_deg = -dy * fov_v / 2.0
        return bearing_off_deg, elev_off_deg


# Entry point -------------------------------------------------------------
if __name__ == "__main__":
    WatcherApp().run() 