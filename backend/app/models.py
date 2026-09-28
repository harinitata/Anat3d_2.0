"""Plain data types shared by every module. No MediaPipe / OpenCV imports here."""
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class Gesture(str, Enum):
    ROTATE_LEFT = "ROTATE_LEFT"
    ROTATE_RIGHT = "ROTATE_RIGHT"
    ZOOM_IN = "ZOOM_IN"
    ZOOM_OUT = "ZOOM_OUT"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Point:
    x: float  # normalised 0-1
    y: float


HandLandmarks = Sequence[Point]  # 21 points, MediaPipe ordering

# MediaPipe landmark indices
THUMB_TIP = 4
INDEX_TIP = 8


@dataclass(frozen=True)
class GestureEvent:
    """What the controller emits. The JSON wire format is decided in step 3."""
    gesture: Gesture
    timestamp: float
