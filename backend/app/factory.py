"""Assembles a GestureController from its parts (dependency injection lives here)."""
from typing import Optional

from .classifiers import ThumbIndexClassifier
from .config import AppConfig
from .controller import GestureController
from .publishers import ConsolePublisher, EventPublisher
from .sources import WebcamSource
from .stabilizer import CooldownGate, GestureStabilizer
from .tracker import HandTracker


def build_controller(cfg: AppConfig, publisher: Optional[EventPublisher] = None) -> GestureController:
    source = WebcamSource(cfg.camera)
    try:
        tracker = HandTracker(cfg.tracking)
    except Exception:
        source.release()          # don't leak the camera if MediaPipe fails to start
        raise
    return GestureController(
        source=source,
        tracker=tracker,
        classifiers=[ThumbIndexClassifier(cfg.gesture)],
        stabilizer=GestureStabilizer(cfg.gesture.stability_frames),
        gate=CooldownGate(cfg.gesture),
        publisher=publisher or ConsolePublisher(),
    )
