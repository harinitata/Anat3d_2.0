"""Where events go. Step 4 adds WebSocketPublisher here without touching anything else."""
from abc import ABC, abstractmethod

from .models import GestureEvent


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: GestureEvent) -> None: ...


class ConsolePublisher(EventPublisher):
    def publish(self, event: GestureEvent) -> None:
        print(f"[{event.timestamp:.2f}] {event.gesture.value}")


class CompositePublisher(EventPublisher):
    """Fan one event out to several publishers (e.g. console log + WebSocket)."""

    def __init__(self, publishers):
        self._publishers = list(publishers)

    def publish(self, event: GestureEvent) -> None:
        for p in self._publishers:
            p.publish(event)
