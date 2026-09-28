from app.models import Gesture, GestureEvent
from app.protocol import event_to_message


def test_protocol_mapping():
    assert event_to_message(GestureEvent(Gesture.ROTATE_LEFT, 1.0)) == \
        {"action": "rotate", "direction": "left", "ts": 1.0}
    assert event_to_message(GestureEvent(Gesture.ZOOM_IN, 2.0))["direction"] == "in"
    assert event_to_message(GestureEvent(Gesture.HOLD, 3.0)) is None
