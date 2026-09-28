"""All tunable numbers live here. Server settings can be overridden with ANAT3D_* env vars."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 320
    height: int = 240
    fps: int = 30


@dataclass(frozen=True)
class TrackingConfig:
    process_every_n_frames: int = 3   # run MediaPipe on every Nth frame
    detect_width: int = 160           # frame is downscaled before detection
    detect_height: int = 120
    max_misses: int = 5               # missed detections before the hand counts as lost


@dataclass(frozen=True)
class GestureConfig:
    # Landmarks are normalised (0-1). The original both2.py computed thumb.x * 320 * 2, so its
    # thresholds were effectively tuned in a 640x480 space. Kept to preserve behaviour.
    ref_width: int = 640
    ref_height: int = 480
    rotation_deadzone: float = 20
    zoom_threshold: float = 70
    stability_frames: int = 2         # agreeing *fresh detections* required
    rotation_interval: float = 0.1    # min seconds between rotate events
    zoom_interval: float = 0.15       # min seconds between zoom events


@dataclass(frozen=True)
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"           # use 0.0.0.0 inside Docker
    port: int = 8000
    mode: str = "webcam"              # "webcam" (real tracking) or "demo" (fake gestures)
    preview: bool = False             # OpenCV debug window (webcam mode)
    autostart: bool = False           # start gesture tracking at boot instead of via the API
    cors_origins: Tuple[str, ...] = ("http://localhost:5173", "http://localhost:3000")
    frontend_dist: Optional[Path] = None   # built React app to serve at "/"

    def __post_init__(self) -> None:
        if self.mode not in ("webcam", "demo"):
            raise ValueError(f"mode must be 'webcam' or 'demo', got {self.mode!r}")

    @classmethod
    def from_env(cls) -> "ServerConfig":
        d, env = cls(), os.environ
        origins = env.get("ANAT3D_CORS_ORIGINS")
        dist = env.get("ANAT3D_FRONTEND_DIST")
        return cls(
            host=env.get("ANAT3D_HOST", d.host),
            port=int(env.get("ANAT3D_PORT", d.port)),
            mode=env.get("ANAT3D_MODE", d.mode),
            cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()) if origins else d.cors_origins,
            frontend_dist=Path(dist) if dist else None,
        )
