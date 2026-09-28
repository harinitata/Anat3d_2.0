"""Owns the background thread of a GestureProducer, with a safe start/stop lifecycle."""
import logging
import threading
from typing import Callable, Optional

from .producers import GestureProducer

log = logging.getLogger("anat3d")


class GestureRunner:
    def __init__(self, factory: Callable[[], GestureProducer], mode: str):
        self.mode = mode
        self._factory = factory
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._error: Optional[str] = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {"running": self.running, "mode": self.mode, "error": self._error}

    def start(self) -> bool:
        """Start tracking. Returns False if already running. Raises if the producer can't open."""
        with self._lock:
            if self.running:
                return False
            self._error = None
            producer = self._factory()
            producer.open()
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, args=(producer,),
                                            daemon=True, name="gesture-producer")
            self._thread.start()
            log.info("gesture tracking started (%s)", self.mode)
            return True

    def stop(self) -> bool:
        """Stop tracking. Returns False if it wasn't running."""
        with self._lock:
            thread = self._thread
            if not self.running:
                return False
            self._stop.set()
        thread.join(timeout=3)
        log.info("gesture tracking stopped")
        return True

    def _run(self, producer: GestureProducer) -> None:
        try:
            producer.run(self._stop)
        except Exception as exc:      # e.g. camera unplugged mid-run
            log.exception("gesture producer crashed")
            self._error = str(exc)
        finally:
            producer.close()
