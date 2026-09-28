"""ANAT3D backend.

    python -m app.server --mode demo --autostart      fake gestures, no camera
    python -m app.server --mode webcam --preview --autostart

REST:  GET /api/health   GET /api/gestures/status   POST /api/gestures/start|stop
WS:    /ws   (gesture events, see docs/protocol.md)
"""
import argparse
import asyncio
import dataclasses
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import ServerConfig
from .hub import Hub
from .producers import GestureProducer, create_producer
from .runner import GestureRunner

log = logging.getLogger("anat3d")

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BACKEND_DIR / "demo"
DEFAULT_FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"


def create_app(cfg: Optional[ServerConfig] = None,
               producer_factory: Optional[Callable[[Hub], GestureProducer]] = None) -> FastAPI:
    cfg = cfg or ServerConfig()
    hub = Hub()
    factory = producer_factory or (lambda h: create_producer(cfg.mode, h, cfg.preview))
    runner = GestureRunner(lambda: factory(hub), cfg.mode)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        hub.attach_loop(asyncio.get_running_loop())
        if cfg.autostart:
            try:
                runner.start()
            except Exception:
                log.exception("autostart failed")
        yield
        runner.stop()

    app = FastAPI(title="ANAT3D backend", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(cfg.cors_origins),
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/gestures/status")
    def gestures_status():
        return runner.status()

    # plain `def` (not async): opening the camera blocks, so FastAPI runs these in a worker thread
    @app.post("/api/gestures/start")
    def gestures_start():
        try:
            started = runner.start()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Could not start gesture tracking: {exc}")
        return {"started": started, **runner.status()}

    @app.post("/api/gestures/stop")
    def gestures_stop():
        stopped = runner.stop()
        return {"stopped": stopped, **runner.status()}

    @app.post("/api/debug/highlight/{name}")
    async def debug_highlight(name: str):
        """Test hook for the backend->browser highlight path."""
        await hub.broadcast({"action": "highlight", "id": name})
        return {"sent": name}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await hub.connect(ws)
        try:
            while True:
                await ws.receive_text()   # ignore client messages; keeps the socket open
        except WebSocketDisconnect:
            pass
        finally:
            hub.disconnect(ws)

    app.mount("/demo", StaticFiles(directory=DEMO_DIR, html=True), name="demo")
    dist = cfg.frontend_dist or DEFAULT_FRONTEND_DIST
    if dist.is_dir():                     # serve the built React app when it exists
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    else:
        @app.get("/")
        def root():
            return {"name": "ANAT3D backend", "docs": "/docs", "demo": "/demo/"}
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="ANAT3D backend")
    parser.add_argument("--mode", choices=["webcam", "demo"])
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--preview", action="store_true", help="OpenCV debug window (webcam mode)")
    parser.add_argument("--autostart", action="store_true", help="start gesture tracking at boot")
    args = parser.parse_args()

    overrides = {k: v for k, v in vars(args).items() if v not in (None, False)}
    cfg = dataclasses.replace(ServerConfig.from_env(), **overrides)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    uvicorn.run(create_app(cfg), host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    main()
