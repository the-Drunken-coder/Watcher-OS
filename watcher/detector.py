from pathlib import Path
from typing import List, Tuple

import numpy as np
import cv2

try:
    from tflite_runtime.interpreter import Interpreter  # type: ignore
except ImportError:
    # Fallback to full TensorFlow if tflite_runtime wheel not installed.
    from tensorflow.lite.python.interpreter import Interpreter  # type: ignore


class Detection:
    """Represents a single object detection result."""

    def __init__(self, bbox: Tuple[int, int, int, int], score: float, class_id: int):
        self.bbox = bbox  # xmin, ymin, xmax, ymax in pixel coords
        self.score = score
        self.class_id = class_id

    def __repr__(self) -> str:
        return f"Detection(cls={self.class_id}, score={self.score:.2f}, bbox={self.bbox})"


class Detector:
    """Lightweight TFLite detector focused on person class."""

    DEFAULT_MODEL = (
        Path(__file__).parent / "models" / "ssd_mobilenet_v2_fpnlite_320x320.tflite"
    )

    # COCO 2017 class IDs for the objects we care about
    COCO_LABELS: dict[int, str] = {
        0: "person",
        2: "car",
        7: "truck",  # treat as car-like
        16: "dog",    # will also approximate coyotes
    }

    def __init__(
        self,
        model_path: Path | str | None = None,
        score_threshold: float = 0.5,
        class_whitelist: set[int] | None = None,
    ):
        model_path = Path(model_path) if model_path else self.DEFAULT_MODEL
        if not model_path.exists():
            raise FileNotFoundError(
                f"TFLite model not found at {model_path}. Copy or download it before running."
            )
        self._interpreter = Interpreter(model_path=str(model_path))
        self._interpreter.allocate_tensors()
        input_details = self._interpreter.get_input_details()
        output_details = self._interpreter.get_output_details()
        self._input_index = input_details[0]["index"]
        self._output_details = output_details
        self._input_shape = input_details[0]["shape"]  # (1, h, w, 3)
        self.score_threshold = score_threshold
        self._class_whitelist = class_whitelist or set(self.COCO_LABELS.keys())

    # ---------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run inference on one RGB frame. Returns detections above threshold."""
        # Resize to model input
        input_h, input_w = self._input_shape[1:3]
        resized = cv2.resize(frame, (input_w, input_h))
        input_tensor = np.expand_dims(resized, axis=0).astype(np.uint8)
        self._interpreter.set_tensor(self._input_index, input_tensor)
        self._interpreter.invoke()

        # Extract outputs (assuming standard TFLite SSD order)
        boxes = self._interpreter.get_tensor(self._output_details[0]["index"])[0]  # (N, 4)
        classes = self._interpreter.get_tensor(self._output_details[1]["index"])[0].astype(int)
        scores = self._interpreter.get_tensor(self._output_details[2]["index"])[0]
        results: List[Detection] = []
        h, w, _ = frame.shape
        for bbox, cls_id, score in zip(boxes, classes, scores):
            if score < self.score_threshold or cls_id not in self._class_whitelist:
                continue
            ymin, xmin, ymax, xmax = bbox
            results.append(
                Detection(
                    bbox=(int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)),
                    score=float(score),
                    class_id=int(cls_id),
                )
            )
        return results 