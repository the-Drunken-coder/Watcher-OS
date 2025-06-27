import logging
import signal
import time

from .camera import Camera
from .detector import Detector
from .serial_comm import Message, SerialWorker
from .geolocate import GeoLocator

logger = logging.getLogger(__name__)

class WatcherEngine:
    """
    The core engine of the Watcher OS.
    This class orchestrates the camera, detector, and serial communication.
    """

    def __init__(self):
        logger.info("Initializing Watcher Engine...")
        self.camera = Camera()
        self.detector = Detector()
        self.serial_worker = SerialWorker()
        self.geolocator = GeoLocator()
        self._running = False
        self._setup_signal_handling()
        logger.info("Watcher Engine Initialized.")

    def run(self):
        """Starts the main loop of the watcher engine."""
        self._running = True
        self.serial_worker.start()

        logger.info("Watcher Engine is running...")
        for frame in self.camera.frames():
            if not self._running:
                break

            own_state = self._get_own_state()
            detections = self.detector.detect(frame)

            if detections and own_state:
                # For simplicity, use center of first bbox
                detection = detections[0]
                xmin, ymin, xmax, ymax = detection.bbox
                cx = (xmin + xmax) / 2
                cy = (ymin + ymax) / 2

                bearing, elevation = self._pixel_to_angles(cx, cy, frame.shape)
                
                tgt_lat, tgt_lon = self.geolocator.locate_target(
                    own_lat=own_state["lat"],
                    own_lon=own_state["lon"],
                    own_alt_msl=own_state["alt"],
                    bearing_deg=bearing,
                    elevation_deg=elevation,
                )

                message = Message(
                    kind="T",
                    payload={
                        "lat": tgt_lat,
                        "lon": tgt_lon,
                        "cls": detection.class_id,
                        "conf": detection.score,
                        "ts": time.time(),
                    },
                )
                self.serial_worker.send(message)

        self.shutdown()

    def _get_own_state(self):
        """Checks for control messages (ownship state)."""
        msg = self.serial_worker.recv_nowait()
        if msg and msg.kind == "S":
            # expects lat, lon, alt, heading, pitch, roll
            return msg.payload
        return None

    def _pixel_to_angles(self, px: float, py: float, shape):
        """Convert pixel location to bearing/elevation offset."""
        h, w, _ = shape
        # Camera horizontal/vertical Field-of-View in degrees (Sony IMX477 std lens)
        fov_h = 62.2
        fov_v = 48.8

        dx = (px - w / 2) / (w / 2)
        dy = (py - h / 2) / (h / 2)

        bearing_off_deg = dx * fov_h / 2.0
        elev_off_deg = -dy * fov_v / 2.0
        return bearing_off_deg, elev_off_deg

    def _setup_signal_handling(self):
        """Sets up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handles signals for graceful shutdown."""
        logger.info(f"Signal {signum} received, shutting down...")
        self._running = False

    def shutdown(self):
        """Shuts down the watcher engine and cleans up resources."""
        logger.info("Shutting down Watcher Engine...")
        self.serial_worker.stop()
        self.camera.close()
        logger.info("Watcher Engine shut down.") 