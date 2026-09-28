"""Filters that decide when a classified gesture is allowed to become an event."""
from collections import deque
from typing import Dict, Optional

from .config import GestureConfig
from .models import Gesture


class GestureStabilizer:
    """Emits a gesture only after `size` consecutive identical classifications."""

    def __init__(self, size: int):
        self._buf: deque = deque(maxlen=size)

    def update(self, gesture: Gesture) -> Optional[Gesture]:
        self._buf.append(gesture)
        if len(self._buf) == self._buf.maxlen and len(set(self._buf)) == 1:
            return gesture
        return None

    def reset(self) -> None:
        self._buf.clear()


class CooldownGate:
    """Rate-limits events. Left/right share a timer, in/out share a timer (as in both2.py)."""

    def __init__(self, cfg: GestureConfig):
        self._group = {
            Gesture.ROTATE_LEFT: "rotate", Gesture.ROTATE_RIGHT: "rotate",
            Gesture.ZOOM_IN: "zoom", Gesture.ZOOM_OUT: "zoom",
        }
        self._interval: Dict[str, float] = {"rotate": cfg.rotation_interval, "zoom": cfg.zoom_interval}
        self._last: Dict[str, float] = {}

    def allow(self, gesture: Gesture, now: float) -> bool:
        group = self._group.get(gesture)
        if group is None:  # HOLD etc. never produce events
            return False
        if now - self._last.get(group, float("-inf")) > self._interval[group]:
            self._last[group] = now
            return True
        return False
