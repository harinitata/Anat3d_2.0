"""Frame -> hand landmarks. The only place MediaPipe is touched."""
from typing import Optional, Tuple

from .config import TrackingConfig
from .models import HandLandmarks, Point


class HandTracker:
    def __init__(self, cfg: TrackingConfig):
        import mediapipe as mp  # lazy import
        self._cfg = cfg
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0,
        )
        self._count = 0
        self._misses = 0
        self._last: Optional[HandLandmarks] = None

    def track(self, frame_bgr) -> Tuple[Optional[HandLandmarks], bool]:
        """Return (landmarks, fresh). `fresh` is True only when this call ran a new
        detection and found a hand; otherwise landmarks are the last known ones."""
        import cv2
        self._count += 1
        if self._count % self._cfg.process_every_n_frames != 0:
            return self._last, False

        small = cv2.resize(frame_bgr, (self._cfg.detect_width, self._cfg.detect_height))
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)

        if results.multi_hand_landmarks:
            self._last = [Point(l.x, l.y) for l in results.multi_hand_landmarks[0].landmark]
            self._misses = 0
            return self._last, True

        self._misses += 1
        if self._misses > self._cfg.max_misses:
            self._last = None
        return self._last, False

    def close(self) -> None:
        self._hands.close()
