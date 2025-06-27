from __future__ import annotations

import json
import logging
import queue
import threading
from dataclasses import dataclass
from time import sleep
from typing import Any, Dict, Optional

try:
    import serial
except ModuleNotFoundError:
    serial = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class Message:
    kind: str
    payload: Dict[str, Any]

    def dumps(self) -> bytes:
        return (json.dumps({"k": self.kind, "p": self.payload}) + "\n").encode()

    @staticmethod
    def loads(raw: str) -> "Message":
        data = json.loads(raw)
        return Message(kind=data["k"], payload=data["p"])


class SerialWorker(threading.Thread):
    """Background thread for non-blocking serial send/receive with newline framing."""

    def __init__(self, device: str = "/dev/ttyAMA0", baud: int = 115200):
        super().__init__(daemon=True)
        if serial and device != "stub":
            try:
                self.ser = serial.Serial(device, baudrate=baud, timeout=0.1)
            except (serial.SerialException, OSError) as exc:  # type: ignore[attr-defined]
                logger.warning("Serial unavailable (%s), falling back to stub", exc)
                self.ser = _StubSerial()
        else:
            self.ser = _StubSerial()
        self._send_q: "queue.Queue[Message]" = queue.Queue()
        self._recv_q: "queue.Queue[Message]" = queue.Queue()
        self._running = True

    # Public API -----------------------------------------------------------
    def send(self, msg: Message):
        self._send_q.put(msg)

    def recv_nowait(self) -> Optional[Message]:
        try:
            return self._recv_q.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        self._running = False

    # Thread main loop -----------------------------------------------------
    def run(self):
        buff = bytearray()
        while self._running:
            # Handle outgoing
            try:
                msg = self._send_q.get_nowait()
                self.ser.write(msg.dumps())
            except queue.Empty:
                pass

            # Handle incoming
            data = self.ser.read(64)
            if data:
                buff.extend(data)
                if b"\n" in buff:
                    lines = buff.split(b"\n")
                    *completed, buff = lines[:-1], lines[-1]
                    for raw in completed:
                        if not raw:
                            continue
                        try:
                            self._recv_q.put(Message.loads(raw.decode()))
                        except Exception as exc:
                            logger.warning("Bad message: %s", exc)
            sleep(0.005)


class _StubSerial:
    """In-memory replacement for Serial during desktop testing."""

    def __init__(self):
        self._buf = bytearray()

    # The real pyserial API
    def write(self, b: bytes):
        logger.debug("[STUB SERIAL] write %s", b)
        # For loopback testing, echo nothing.

    def read(self, size: int):
        # No incoming data in stub.
        return b"" 