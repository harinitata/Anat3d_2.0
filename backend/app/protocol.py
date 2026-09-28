"""Wire format (DRAFT, to be agreed with the frontend in step 3).

    {"action": "rotate",    "direction": "left" | "right", "ts": 123.4}
    {"action": "zoom",      "direction": "in"   | "out",   "ts": 123.4}
    {"action": "highlight", "id": "<mesh name>"}
"""
from typing import Optional

from .models import Gesture, GestureEvent

_ACTIONS = {
    Gesture.ROTATE_LEFT: ("rotate", "left"),
    Gesture.ROTATE_RIGHT: ("rotate", "right"),
    Gesture.ZOOM_IN: ("zoom", "in"),
    Gesture.ZOOM_OUT: ("zoom", "out"),
}


def event_to_message(event: GestureEvent) -> Optional[dict]:
    pair = _ACTIONS.get(event.gesture)
    if pair is None:
        return None
    action, direction = pair
    return {"action": action, "direction": direction, "ts": event.timestamp}
