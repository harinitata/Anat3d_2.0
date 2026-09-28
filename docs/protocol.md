# Backend <-> Frontend contract

Backend: FastAPI on `http://localhost:8000` (override with `ANAT3D_PORT`).
CORS is enabled for `http://localhost:5173` (Vite) and `http://localhost:3000` (CRA);
add more with `ANAT3D_CORS_ORIGINS=http://a,http://b`.

## WebSocket `ws://localhost:8000/ws`

The server pushes JSON messages. The client sends nothing.

```json
{ "action": "rotate",    "direction": "left" | "right", "ts": 1790568787.11 }
{ "action": "zoom",      "direction": "in"   | "out",   "ts": 1790568787.21 }
{ "action": "highlight", "id": "<mesh name>" }
```

- `rotate` / `zoom` are **step events**, sent about 10 times a second while the gesture is held.
  The frontend decides how big a step is and should smooth it (ease toward a target value).
  `backend/demo/index.html` shows one way (`Viewer.rotate/zoom` + lerp in the render loop).
- `highlight` is not produced by a gesture yet. It can be triggered for testing with
  `POST /api/debug/highlight/<mesh name>`. `id` must match the mesh name in the `.glb`.
- Unknown `action` values should be ignored, so new message types won't break the UI.

## REST

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/health` | `{"status":"ok"}` |
| GET  | `/api/gestures/status` | `{"running": bool, "mode": "webcam"\|"demo", "error": str\|null}` |
| POST | `/api/gestures/start` | Opens the camera and starts tracking. `{"started": bool, ...status}`. **503** with `detail` if the camera can't open. Calling it while running is harmless (`started:false`). |
| POST | `/api/gestures/stop` | Stops tracking and releases the camera. `{"stopped": bool, ...status}` |
| POST | `/api/debug/highlight/{name}` | Test hook: broadcasts a `highlight` message |

Interactive API docs: `http://localhost:8000/docs`

## What replaced the old Express server (`server.js`, port 5000)

| Old endpoint | New |
|---|---|
| `POST /api/launch-blender` | Removed. The React app loads `.glb` models itself. |
| `POST /api/launch-python` | `POST /api/gestures/start` |
| `POST /api/launch` | Load the heart model in React, then `POST /api/gestures/start` |
| `POST /api/launch-brain` | Load the brain model in React, then `POST /api/gestures/start` |
| `POST /api/launch-mouth` | Load the mouth model in React, then `POST /api/gestures/start` |

Which organ is shown is now purely a frontend decision. The backend does not care.

## React sketch

```jsx
import { useEffect, useRef } from "react";

// Vite: import.meta.env.VITE_WS_URL   |   CRA: process.env.REACT_APP_WS_URL
const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws";

export function useGestureSocket(onMessage) {
  const handler = useRef(onMessage);
  handler.current = onMessage;                      // always call the latest callback

  useEffect(() => {
    let ws, retry, closed = false;
    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onmessage = (e) => handler.current(JSON.parse(e.data));
      ws.onclose = () => { if (!closed) retry = setTimeout(connect, 2000); };
    };
    connect();
    return () => { closed = true; clearTimeout(retry); ws.close(); };
  }, []);
}

// usage
useGestureSocket((msg) => {
  if (msg.action === "rotate") rotateModel(msg.direction);
  else if (msg.action === "zoom") zoomModel(msg.direction);
  else if (msg.action === "highlight") highlightPart(msg.id);
});

// start / stop button
await fetch("http://localhost:8000/api/gestures/start", { method: "POST" });
```
