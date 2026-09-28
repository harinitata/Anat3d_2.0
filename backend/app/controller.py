"""Orchestrates source -> tracker -> classifiers -> stabilizer -> gate -> publisher."""
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from .classifiers import GestureClassifier
from .models import Gesture, GestureEvent
from .publishers import EventPublisher
from .sources import FrameSource
from .stabilizer import CooldownGate, GestureStabilizer


@dataclass
class FrameResult:
    frame: Optional[Any]
    hand_detected: bool
    gesture: Optional[Gesture]      # latest raw classification (for the preview overlay)
    event: Optional[GestureEvent]   # set only if an event was published this step


class GestureController:
    def __init__(self, source: FrameSource, tracker, classifiers: List[GestureClassifier],
                 stabilizer: GestureStabilizer, gate: CooldownGate, publisher: EventPublisher,
                 clock: Callable[[], float] = time.time):
        self._source, self._tracker = source, tracker
        self._classifiers, self._stabilizer = classifiers, stabilizer
        self._gate, self._publisher, self._clock = gate, publisher, clock
        self._last_gesture: Optional[Gesture] = None

    def step(self) -> FrameResult:
        frame = self._source.read()
        if frame is None:
            return FrameResult(None, False, None, None)

        hand, fresh = self._tracker.track(frame)
        if hand is None:
            self._stabilizer.reset()
            self._last_gesture = None
            return FrameResult(frame, False, None, None)

        event = None
        if fresh:  # only classify new detections, never stale landmarks
            self._last_gesture = self._classify(hand)
            stable = self._stabilizer.update(self._last_gesture)
            now = self._clock()
            if stable is not None and self._gate.allow(stable, now):
                event = GestureEvent(stable, now)
                self._publisher.publish(event)
        return FrameResult(frame, True, self._last_gesture, event)

    def _classify(self, hand) -> Gesture:
        for classifier in self._classifiers:   # first classifier with an opinion wins
            gesture = classifier.classify(hand)
            if gesture is not None:
                return gesture
        return Gesture.HOLD

    def close(self) -> None:
        self._source.release()
        close = getattr(self._tracker, "close", None)
        if close:
            close()
