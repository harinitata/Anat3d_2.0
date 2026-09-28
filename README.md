# ANAT3D

Gesture-controlled 3D anatomy viewer. A webcam tracks your hand (MediaPipe), the Python backend turns
it into rotate / zoom events, and the browser applies them to a 3D model over a WebSocket.
No mouse or keyboard needed.

```
webcam -> MediaPipe -> gesture classifier -> stabilizer -> WebSocket -> React + Three.js viewer
```

## Layout

```
backend/    FastAPI + gesture recognition (Python)
  app/        the application code (see below)
  demo/       tiny vanilla Three.js page to test the backend without React  -> /demo/
  tests/
frontend/   React app
docs/       protocol.md: WebSocket + REST contract between the two
```

### Backend modules (`backend/app/`)

| File | Role |
|---|---|
| `config.py` | Every tunable number, plus env-driven `ServerConfig` |
| `models.py` | Shared data types (`Gesture`, `Point`, `GestureEvent`) |
| `sources.py` | `FrameSource` (abstract) -> `WebcamSource` |
| `tracker.py` | `HandTracker`: MediaPipe wrapper |
| `classifiers.py` | `GestureClassifier` (abstract) -> `ThumbIndexClassifier` |
| `stabilizer.py` | `GestureStabilizer`, `CooldownGate` |
| `controller.py` | `GestureController`: runs the pipeline, one `step()` per frame |
| `factory.py` | Assembles a controller from its parts |
| `publishers.py` | `EventPublisher` (abstract) -> console / composite |
| `protocol.py`, `hub.py` | Event -> JSON, and broadcasting to connected browsers |
| `producers.py` | `GestureProducer` (abstract) -> `WebcamProducer`, `DemoProducer` |
| `runner.py` | `GestureRunner`: safe start/stop of the background thread |
| `server.py` | FastAPI app: REST, WebSocket, static files |

## Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows   (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt

python -m app.server --mode demo --autostart      # fake gestures, no camera needed
python -m app.server --mode webcam --preview --autostart   # real hand tracking
```

Open http://localhost:8000/demo/ to see it working, and http://localhost:8000/docs for the API.
Without `--autostart`, tracking starts when the frontend calls `POST /api/gestures/start`.

Environment variables: `ANAT3D_HOST`, `ANAT3D_PORT`, `ANAT3D_MODE` (`webcam`|`demo`),
`ANAT3D_CORS_ORIGINS`, `ANAT3D_FRONTEND_DIST`.

## Tests

```bash
cd backend && python -m pytest
```
