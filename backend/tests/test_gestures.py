from app.classifiers import ThumbIndexClassifier
from app.config import GestureConfig
from app.controller import GestureController
from app.models import Gesture, Point, THUMB_TIP, INDEX_TIP
from app.publishers import EventPublisher
from app.stabilizer import CooldownGate, GestureStabilizer

CFG = GestureConfig()


def hand(thumb, index):
    pts = [Point(0.5, 0.5)] * 21
    pts = list(pts)
    pts[THUMB_TIP], pts[INDEX_TIP] = Point(*thumb), Point(*index)
    return pts


# ---- classifier (thresholds in 640x480 space: 0.05 -> 32px, 0.03 -> 19px) ----
def test_rotate_right_and_left():
    c = ThumbIndexClassifier(CFG)
    assert c.classify(hand((0.6, 0.5), (0.5, 0.5))) == Gesture.ROTATE_RIGHT
    assert c.classify(hand((0.5, 0.5), (0.6, 0.5))) == Gesture.ROTATE_LEFT


def test_rotation_deadzone_is_hold():
    assert ThumbIndexClassifier(CFG).classify(hand((0.52, 0.5), (0.5, 0.5))) == Gesture.HOLD


def test_zoom_by_finger_distance():
    c = ThumbIndexClassifier(CFG)
    assert c.classify(hand((0.5, 0.5), (0.5, 0.8))) == Gesture.ZOOM_IN    # 144px apart
    assert c.classify(hand((0.5, 0.5), (0.5, 0.55))) == Gesture.ZOOM_OUT  # 24px apart


# ---- stabilizer ----
def test_stabilizer_needs_consecutive_agreement():
    s = GestureStabilizer(3)
    assert s.update(Gesture.ZOOM_IN) is None
    assert s.update(Gesture.ZOOM_IN) is None
    assert s.update(Gesture.ZOOM_IN) == Gesture.ZOOM_IN
    assert s.update(Gesture.ROTATE_LEFT) is None        # flicker breaks it


def test_stabilizer_reset():
    s = GestureStabilizer(2)
    s.update(Gesture.ZOOM_IN)
    s.reset()
    assert s.update(Gesture.ZOOM_IN) is None


# ---- cooldown gate ----
def test_gate_rate_limits_and_shares_group_timer():
    g = CooldownGate(CFG)
    assert g.allow(Gesture.ROTATE_LEFT, 1.0)
    assert not g.allow(Gesture.ROTATE_RIGHT, 1.05)      # same group, too soon
    assert g.allow(Gesture.ZOOM_IN, 1.05)               # different group, independent
    assert g.allow(Gesture.ROTATE_RIGHT, 1.2)
    assert not g.allow(Gesture.HOLD, 5.0)


# ---- controller wiring with fakes ----
class FakeSource:
    def read(self): return "frame"
    def release(self): pass


class FakeTracker:
    def __init__(self, seq): self.seq = iter(seq)
    def track(self, frame): return next(self.seq)


class Collector(EventPublisher):
    def __init__(self): self.events = []
    def publish(self, e): self.events.append(e)


def make_controller(seq, stability=2):
    pub, t = Collector(), [0.0]
    def clock():
        t[0] += 0.2
        return t[0]
    ctl = GestureController(FakeSource(), FakeTracker(seq), [ThumbIndexClassifier(CFG)],
                            GestureStabilizer(stability), CooldownGate(CFG), pub, clock)
    return ctl, pub


def test_controller_publishes_after_stable_fresh_detections():
    h = hand((0.6, 0.5), (0.5, 0.5))
    ctl, pub = make_controller([(h, True), (h, True), (h, True)])
    for _ in range(3):
        ctl.step()
    assert [e.gesture for e in pub.events] == [Gesture.ROTATE_RIGHT, Gesture.ROTATE_RIGHT]


def test_controller_ignores_stale_landmarks():
    h = hand((0.6, 0.5), (0.5, 0.5))
    ctl, pub = make_controller([(h, True), (h, False), (h, False), (h, False)])
    for _ in range(4):
        ctl.step()
    assert pub.events == []   # only one fresh detection -> stability (2) never reached


def test_controller_resets_when_hand_lost():
    h = hand((0.6, 0.5), (0.5, 0.5))
    ctl, pub = make_controller([(h, True), (None, False), (h, True)])
    for _ in range(3):
        ctl.step()
    assert pub.events == []   # loss cleared the buffer, so 2nd fresh detection is only 1 in a row
