"""Sources of gesture events. The server only knows the GestureProducer interface."""
import threading
import time
from abc import ABC, abstractmethod

from .config import AppConfig
from .hub import Hub, HubPublisher
from .models import Gesture, GestureEvent
from .publishers import CompositePublisher, ConsolePublisher, EventPublisher


class GestureProducer(ABC):
    def open(self) -> None:
        """Acquire resources (camera...). Called synchronously; raise if it can't work."""

    @abstractmethod
    def run(self, stop: threading.Event) -> None:
        """Produce events until `stop` is set. Runs on a background thread."""

    def close(self) -> None:
        """Release resources."""


class DemoProducer(GestureProducer):
    """Fake gestures, so the web side can be tested without a camera."""

    SCRIPT = ([Gesture.ROTATE_RIGHT] * 20 + [Gesture.ZOOM_IN] * 10 +
              [Gesture.ROTATE_LEFT] * 20 + [Gesture.ZOOM_OUT] * 10)

    def __init__(self, publisher: EventPublisher, interval: float = 0.1):
        self._publisher, self._interval = publisher, interval

    def run(self, stop: threading.Event) -> None:
        while not stop.is_set():
            for gesture in self.SCRIPT:
                if stop.is_set():
                    return
                self._publisher.publish(GestureEvent(gesture, time.time()))
                time.sleep(self._interval)


class WebcamProducer(GestureProducer):
    """Real hand tracking: webcam -> MediaPipe -> gestures."""

    def __init__(self, publisher: EventPublisher, cfg: AppConfig, preview: bool = False):
        self._publisher, self._cfg, self._preview_on = publisher, cfg, preview
        self._controller = None
        self._preview = None

    def open(self) -> None:
        from .factory import build_controller      # lazy: demo mode needs no OpenCV/MediaPipe
        self._controller = build_controller(self._cfg, self._publisher)

    def run(self, stop: threading.Event) -> None:
        if self._preview_on:
            from .preview import Preview
            self._preview = Preview()
        while not stop.is_set():
            result = self._controller.step()
            if result.frame is None:
                time.sleep(0.01)
            if self._preview and not self._preview.show(result):   # ESC closes the window only
                self._preview.close()
                self._preview = None

    def close(self) -> None:
        if self._preview:
            self._preview.close()
            self._preview = None
        if self._controller:
            self._controller.close()
            self._controller = None


def create_producer(mode: str, hub: Hub, preview: bool = False) -> GestureProducer:
    hub_publisher = HubPublisher(hub)
    if mode == "demo":
        return DemoProducer(hub_publisher)
    return WebcamProducer(CompositePublisher([ConsolePublisher(), hub_publisher]), AppConfig(), preview)
