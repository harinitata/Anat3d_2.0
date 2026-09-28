"""Where frames come from. Abstract so a network/video-file source can replace the webcam."""
from abc import ABC, abstractmethod
from typing import Any, Optional

from .config import CameraConfig


class FrameSource(ABC):
    @abstractmethod
    def read(self) -> Optional[Any]:
        """Return the next BGR frame, or None if unavailable."""

    @abstractmethod
    def release(self) -> None: ...


class WebcamSource(FrameSource):
    def __init__(self, cfg: CameraConfig):
        import cv2  # lazy: keeps the rest of the package importable without OpenCV
        self._cap = cv2.VideoCapture(cfg.index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.height)
        self._cap.set(cv2.CAP_PROP_FPS, cfg.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self._cap.isOpened():
            self._cap.release()
            raise RuntimeError(f"Could not open camera {cfg.index}")

    def read(self):
        ok, frame = self._cap.read()
        return frame if ok else None

    def release(self) -> None:
        self._cap.release()
