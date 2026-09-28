"""Landmarks -> gesture. Pure logic, no I/O, fully unit-testable."""
import math
from abc import ABC, abstractmethod
from typing import Optional

from .config import GestureConfig
from .models import Gesture, HandLandmarks, INDEX_TIP, THUMB_TIP


class GestureClassifier(ABC):
    @abstractmethod
    def classify(self, hand: HandLandmarks) -> Optional[Gesture]:
        """Return a gesture, or None if this classifier has no opinion."""


class ThumbIndexClassifier(GestureClassifier):
    """The rotate/zoom logic from both2.py's get_gesture(), unchanged in behaviour:
    horizontal thumb-index offset -> rotate, vertical dominance -> zoom by finger distance."""

    def __init__(self, cfg: GestureConfig):
        self._cfg = cfg

    def classify(self, hand: HandLandmarks) -> Gesture:
        thumb, index = hand[THUMB_TIP], hand[INDEX_TIP]
        dx = (thumb.x - index.x) * self._cfg.ref_width
        dy = (thumb.y - index.y) * self._cfg.ref_height

        if abs(dx) > abs(dy):
            if abs(dx) > self._cfg.rotation_deadzone:
                return Gesture.ROTATE_RIGHT if dx > 0 else Gesture.ROTATE_LEFT
            return Gesture.HOLD
        return Gesture.ZOOM_IN if math.hypot(dx, dy) > self._cfg.zoom_threshold else Gesture.ZOOM_OUT
