from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Dict, Any
import os
import yaml

def get_config_path() -> Path:
    # daksha_data_collection's own config, separate from daksha_ui's
    # config/project.config.yaml — each package owns its config, no
    # cross-package file.
    return Path(__file__).parent.parent / "config" / "config.yaml"

def load_yaml_config(path: str | Path | None = None) -> Dict[str, Any]:
    config_path = Path(path) if path else get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


VCodec = Literal[
    "h264",
    "hevc",
    "libsvtav1",
    "auto",
    "h264_videotoolbox",
    "h264_nvenc",
]


@dataclass(frozen=True)
class CameraSpec:
    key: str
    height: int = 240
    width: int = 320
    channels: int = 3
    role: Literal["main", "wrist", "world", "front_left", "front_right", "secondary"] = (
        "secondary"
    )
    enabled: bool = True

    @property
    def chw_shape(self) -> tuple[int, int, int]:
        return (self.channels, self.height, self.width)

    @property
    def hwc_shape(self) -> tuple[int, int, int]:
        return (self.height, self.width, self.channels)


@dataclass(frozen=True)
class V3FeatureSpec:
    action_dim: int
    follower_state_dim: int
    leader_state_dim: int
    joint_names: tuple[str, ...] = ()
    include_follower_state_duplicate: bool = False


@dataclass
class V3DatasetConfig:
    repo_id: str
    root: Path
    fps: int = 30
    robot_type: str = "custom_robot"
    cameras: list[CameraSpec] = field(default_factory=list)
    feature_spec: V3FeatureSpec = field(
        default_factory=lambda: V3FeatureSpec(
            action_dim=7,
            follower_state_dim=7,
            leader_state_dim=7,
        )
    )
    use_videos: bool = True
    vcodec: VCodec = "libsvtav1"
    batch_encoding_size: int = 1
    streaming_encoding: bool = True
    encoder_queue_maxsize: int = 30
    encoder_threads: int | None = None
    image_writer_processes: int = 0
    image_writer_threads_per_camera: int = 2

    @property
    def enabled_cameras(self) -> list[CameraSpec]:
        return [c for c in self.cameras if c.enabled]


@dataclass(frozen=True)
class ReplayConfig:
    repo_id: str
    root: Path
    episodes: list[int] | None = None
    video_backend: str | None = None
    download_videos: bool = True

