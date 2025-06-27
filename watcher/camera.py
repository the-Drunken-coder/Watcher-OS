import time
from typing import Iterator, Tuple

import cv2
import numpy as np
from picamera2 import Picamera2, Preview


class Camera:
    """Thin wrapper around Picamera2 to yield RGB frames as numpy arrays."""

    def __init__(self, resolution: Tuple[int, int] = (640, 480), framerate: int = 30):
        self._picam = Picamera2()
        # Configure camera
        video_config = self._picam.create_video_configuration(
            main={"size": resolution, "format": "RGB888"}, controls={"FrameRate": framerate}
        )
        self._picam.configure(video_config)
        self._picam.start()
        # Warm-up delay for auto-exposure etc.
        time.sleep(2)

    def frames(self) -> Iterator[np.ndarray]:
        """Infinite generator yielding frames (RGB numpy arrays)."""
        while True:
            frame = self._picam.capture_array()
            yield frame

    def close(self):
        self._picam.close() 