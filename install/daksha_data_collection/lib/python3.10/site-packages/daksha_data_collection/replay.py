from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import av
import pandas as pd

try:
    from .config import ReplayConfig
except ImportError:
    from config import ReplayConfig


@dataclass
class ReplayItem:
    index: int
    episode_index: int
    task: str
    item: dict[str, Any]


class V3DatasetReplay:
    """
    Local-only v3-style replay helper.
    Reads parquet rows and synchronized per-camera videos from disk.
    Uses PyAV for decoding so AV1 recordings replay correctly.
    """

    def __init__(self, cfg: ReplayConfig) -> None:
        self.cfg = cfg
        self.root = cfg.root
        self.info = self._read_info()
        self.camera_keys = list(self.info.get("camera_keys", []))
        self.episodes_df = self._read_episodes()
        if cfg.episodes is not None:
            selected = set(cfg.episodes)
            self.episodes_df = self.episodes_df[
                self.episodes_df["episode_index"].isin(selected)
            ].reset_index(drop=True)

        self._episode_lengths = {
            int(row["episode_index"]): int(row["length"])
            for _, row in self.episodes_df.iterrows()
        }
        self._global_length = int(sum(self._episode_lengths.values()))

    def __len__(self) -> int:
        return self._global_length

    def __getitem__(self, idx: int) -> dict[str, Any]:
        if idx < 0 or idx >= len(self):
            raise IndexError(idx)

        offset = 0
        for _, row in self.episodes_df.iterrows():
            episode_index = int(row["episode_index"])
            episode_len = int(row["length"])
            if idx < offset + episode_len:
                frame_index = idx - offset
                return self._load_frame(episode_index, frame_index)
            offset += episode_len
        raise IndexError(idx)

    def iter_all(self) -> Iterator[ReplayItem]:
        global_index = 0
        for _, episode_row in self.episodes_df.iterrows():
            episode_index = int(episode_row["episode_index"])
            for item in self.iter_episode(episode_index):
                yield ReplayItem(
                    index=global_index,
                    episode_index=item.episode_index,
                    task=item.task,
                    item=item.item,
                )
                global_index += 1

    def iter_episode(
        self, episode_index: int, cancel_event: Optional[threading.Event] = None
    ) -> Iterator[ReplayItem]:
        """`cancel_event`: checked once per step so a caller decoding this on
        a background thread (see ros2_topic_replay.py's _load_episode) can
        abort a long-running load early -- decoding every frame of every
        camera for a whole episode can take tens of seconds on this rig's
        embedded hardware, and without a way to cut it short, Stop had
        nothing to cancel."""
        df = pd.read_parquet(self._parquet_path(episode_index))
        decoders: dict[str, tuple[av.container.InputContainer, Iterator[Any]]] = {}
        try:
            for camera_key in self.camera_keys:
                video_path = self._video_path(episode_index, camera_key)
                if not video_path.exists():
                    continue
                container = av.open(str(video_path))
                decoders[camera_key] = (container, container.decode(video=0))

            for local_index, row in enumerate(df.to_dict("records")):
                if cancel_event is not None and cancel_event.is_set():
                    return
                item = dict(row)
                if "prompt" not in item:
                    item["prompt"] = ""
                for camera_key, (_, frames_iter) in decoders.items():
                    try:
                        frame = next(frames_iter)
                    except StopIteration as exc:
                        raise RuntimeError(
                            f"Replay ended early for camera '{camera_key}' at step {local_index}"
                        ) from exc
                    item[camera_key] = frame.to_ndarray(format="rgb24")
                yield ReplayItem(
                    index=local_index,
                    episode_index=episode_index,
                    task=str(item.get("task", "")),
                    item=item,
                )
        finally:
            for container, _ in decoders.values():
                container.close()

    def _load_frame(self, episode_index: int, frame_index: int) -> dict[str, Any]:
        df = pd.read_parquet(self._parquet_path(episode_index))
        if frame_index < 0 or frame_index >= len(df):
            raise IndexError(frame_index)
        item = dict(df.iloc[frame_index].to_dict())
        if "prompt" not in item:
            item["prompt"] = ""

        for camera_key in self.camera_keys:
            video_path = self._video_path(episode_index, camera_key)
            if not video_path.exists():
                continue
            container = av.open(str(video_path))
            try:
                target_frame = None
                for i, frame in enumerate(container.decode(video=0)):
                    if i == frame_index:
                        target_frame = frame
                        break
                if target_frame is None:
                    raise RuntimeError(
                        f"Could not read frame {frame_index} from {video_path}"
                    )
                item[camera_key] = target_frame.to_ndarray(format="rgb24")
            finally:
                container.close()
        return item

    def _read_info(self) -> dict[str, Any]:
        path = self.root / "meta" / "info.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing info file: {path}")
        return pd.read_json(path, typ="series").to_dict()

    def _read_episodes(self) -> pd.DataFrame:
        path = self.root / "meta" / "episodes" / "chunk-000" / "episodes.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing episodes metadata: {path}")
        return pd.read_parquet(path).sort_values("episode_index").reset_index(drop=True)

    def _parquet_path(self, episode_index: int) -> Path:
        return self.root / "data" / "chunk-000" / f"episode_{episode_index:06d}.parquet"

    def _video_path(self, episode_index: int, camera_key: str) -> Path:
        return (
            self.root
            / "videos"
            / camera_key
            / "chunk-000"
            / f"episode_{episode_index:06d}.mp4"
        )
