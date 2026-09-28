import time

import pytest
from fastapi.testclient import TestClient

from app.config import ServerConfig
from app.producers import GestureProducer
from app.runner import GestureRunner
from app.server import create_app


class BrokenCamera(GestureProducer):
    def open(self):
        raise RuntimeError("Could not open camera 0")

    def run(self, stop):
        pass


class CrashingProducer(GestureProducer):
    def run(self, stop):
        raise RuntimeError("boom")


def demo_client(**kw):
    return TestClient(create_app(ServerConfig(mode="demo", **kw)))


def test_health_and_root():
    with demo_client() as c:
        assert c.get("/api/health").json() == {"status": "ok"}
        assert c.get("/").json()["name"] == "ANAT3D backend"
        assert "ANAT3D" in c.get("/demo/").text


def test_start_streams_events_and_stop_stops():
    with demo_client() as c:
        assert c.get("/api/gestures/status").json()["running"] is False
        with c.websocket_connect("/ws") as ws:
            r = c.post("/api/gestures/start").json()
            assert r["started"] is True and r["running"] is True
            assert c.post("/api/gestures/start").json()["started"] is False   # idempotent
            assert ws.receive_json()["action"] in {"rotate", "zoom"}
            r = c.post("/api/gestures/stop").json()
            assert r["stopped"] is True and r["running"] is False
            assert c.post("/api/gestures/stop").json()["stopped"] is False


def test_start_failure_returns_503_with_reason():
    app = create_app(ServerConfig(mode="demo"), producer_factory=lambda hub: BrokenCamera())
    with TestClient(app) as c:
        r = c.post("/api/gestures/start")
        assert r.status_code == 503 and "Could not open camera 0" in r.json()["detail"]
        assert c.get("/api/gestures/status").json()["running"] is False


def test_runner_records_crash():
    runner = GestureRunner(CrashingProducer, "demo")
    assert runner.start() is True
    for _ in range(50):
        if not runner.running:
            break
        time.sleep(0.02)
    assert runner.status() == {"running": False, "mode": "demo", "error": "boom"}


def test_debug_highlight_reaches_websocket_client():
    with demo_client() as c:
        with c.websocket_connect("/ws") as ws:
            c.post("/api/debug/highlight/left_ventricle")
            assert ws.receive_json() == {"action": "highlight", "id": "left_ventricle"}


def test_cors_allows_react_dev_origin_only():
    with demo_client() as c:
        ok = c.get("/api/health", headers={"Origin": "http://localhost:5173"})
        assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
        bad = c.get("/api/health", headers={"Origin": "http://evil.example"})
        assert "access-control-allow-origin" not in bad.headers


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("ANAT3D_PORT", "9000")
    monkeypatch.setenv("ANAT3D_MODE", "demo")
    monkeypatch.setenv("ANAT3D_CORS_ORIGINS", "http://a.test, http://b.test")
    cfg = ServerConfig.from_env()
    assert (cfg.port, cfg.mode, cfg.cors_origins) == (9000, "demo", ("http://a.test", "http://b.test"))
    with pytest.raises(ValueError):
        ServerConfig(mode="blender")
