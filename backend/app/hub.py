"""Connection hub. The gesture loop runs in a worker thread, the WebSocket server in an
asyncio loop, so publishing from the thread must be thread-safe."""
import asyncio
from typing import Optional, Set

from fastapi import WebSocket

from .models import GestureEvent
from .protocol import event_to_message
from .publishers import EventPublisher


class Hub:
    def __init__(self) -> None:
        self._clients: Set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def broadcast(self, message: dict) -> None:
        for ws in list(self._clients):
            try:
                await ws.send_json(message)
            except Exception:
                self._clients.discard(ws)

    def broadcast_threadsafe(self, message: dict) -> None:
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)


class HubPublisher(EventPublisher):
    """Plugs the gesture pipeline into the hub - same interface as ConsolePublisher."""

    def __init__(self, hub: Hub) -> None:
        self._hub = hub

    def publish(self, event: GestureEvent) -> None:
        message = event_to_message(event)
        if message is not None:
            self._hub.broadcast_threadsafe(message)
