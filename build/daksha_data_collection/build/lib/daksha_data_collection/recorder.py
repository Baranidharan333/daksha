from __future__ import annotations

import json
import queue
import threading
import time
import traceback
from pathlib import Path
from typing import Any

import av
import cv2
import numpy as np
import pandas as pd

try:
    from .config import V3DatasetConfig
    from .features import build_v3_features
except ImportError:
    from config import V3DatasetConfig
    from features import build_v3_features


class V3DatasetRecorder:
    """
    Local-only v3-style dataset recorder.
    Writes parquet episode metadata + per-camera MP4 videos + light meta files.
    """

    _CODEC_MAP = {
        "auto": "h264",
        "h264": "h264",
        "hevc": "hevc",
        "libsvtav1": "libsvtav1",
        "h264_videotoolbox": "h264_videotoolbox",
        "h264_nvenc": "h264_nvenc",
    }

    def __init__(self, cfg: V3DatasetConfig) -> None:
        self.cfg = cfg
        self._episode_rows: list[dict[str, Any]] = []
        self._episode_frames: dict[str, list[np.ndarray]] = {
            cam.key: [] for cam in cfg.enabled_cameras
        }

        # meta/stats.json rebuild re-reads and re-stacks every episode's
        # full parquet data from disk, and used to run synchronously here
        # *and* on every single save_episode() call -- so it got slower as a
        # dataset grew, and resuming a large existing dataset alone
        # (resume_existing() -> this constructor) could already exceed a
        # caller's service-call timeout before a single episode was
        # recorded. Video encoding and meta/info.json stay synchronous
        # (bounded per-episode cost); only the unbounded stats rebuild is
        # deferred, onto a single serialized worker so concurrent rebuilds
        # never race each other on disk.
        self._save_queue: "queue.Queue[Any]" = queue.Queue()
        self._save_worker = threading.Thread(target=self._save_worker_loop, daemon=True)
        self._save_worker.start()

        self._ensure_layout()
        self._num_episodes = self._compute_num_episodes()
        self._num_frames = self._compute_num_frames()
        self._next_episode_index = self._compute_next_episode_index()
        self._rebuild_info_json()
        self._enqueue_stats_rebuild()

    def _save_worker_loop(self) -> None:
        while True:
            task = self._save_queue.get()
            try:
                if task is None:
                    return
                task()
            except Exception:
                traceback.print_exc()
            finally:
                self._save_queue.task_done()

    def _enqueue_stats_rebuild(self) -> None:
        self._save_queue.put(self._rebuild_stats_json)

    def wait_for_pending_saves(self) -> None:
        """Block until every enqueued background stats rebuild has finished.
        Call before relying on meta/stats.json being fully up to date (e.g.
        before finalize() or process exit)."""
        self._save_queue.join()

    @classmethod
    def create_new(cls, cfg: V3DatasetConfig) -> "V3DatasetRecorder":
        recorder = cls(cfg=cfg)
        recorder._initialize_empty_meta()
        recorder._num_episodes = 0
        recorder._num_frames = 0
        recorder._next_episode_index = 0
        recorder._rebuild_info_json()
        recorder._enqueue_stats_rebuild()
        return recorder

    @classmethod
    def resume_existing(cls, cfg: V3DatasetConfig) -> "V3DatasetRecorder":
        return cls(cfg=cfg)

    @property
    def root(self) -> Path:
        return self.cfg.root

    @property
    def num_episodes(self) -> int:
        return self._num_episodes

    @property
    def num_frames(self) -> int:
        return self._num_frames

    @property
    def meta_dir(self) -> Path:
        return self.root / "meta"

    @property
    def info_path(self) -> Path:
        return self.meta_dir / "info.json"

    @property
    def stats_path(self) -> Path:
        return self.meta_dir / "stats.json"

    @property
    def tasks_path(self) -> Path:
        return self.meta_dir / "tasks.parquet"

    @property
    def episodes_path(self) -> Path:
        return self.meta_dir / "episodes" / "chunk-000" / "episodes.parquet"

    @property
    def data_dir(self) -> Path:
        return self.root / "data" / "chunk-000"

    def video_dir(self, camera_key: str) -> Path:
        return self.root / "videos" / camera_key / "chunk-000"

    def add_step(
        self,
        frames_by_camera: dict[str, np.ndarray],
        action: np.ndarray | list[float],
        follower_state: np.ndarray | list[float],
        leader_state: np.ndarray | list[float],
        task: str,
        prompt: str = "",
        timestamp: float | None = None,
        extras: dict[str, Any] | None = None,
    ) -> None:
        row: dict[str, Any] = {
            "timestamp": float(time.time() if timestamp is None else timestamp),
            "action": np.asarray(action, dtype=np.float32).reshape(-1).tolist(),
            "observation.state": np.asarray(
                follower_state, dtype=np.float32
            ).reshape(-1).tolist(),
            "observation.leader_state": np.asarray(
                leader_state, dtype=np.float32
            ).reshape(-1).tolist(),
            "task": str(task),
            "prompt": str(prompt),
        }

        if self.cfg.feature_spec.include_follower_state_duplicate:
            row["observation.follower_state"] = np.asarray(
                follower_state, dtype=np.float32
            ).reshape(-1).tolist()

        if extras:
            for key, value in extras.items():
                if key in row:
                    raise ValueError(f"Extras key '{key}' conflicts with base frame fields")
                row[key] = self._serialize_extra(value)

        for cam in self.cfg.enabled_cameras:
            if cam.key not in frames_by_camera:
                raise KeyError(f"Missing frame for camera key: {cam.key}")
            image = self._normalize_image(frames_by_camera[cam.key], cam.hwc_shape)
            self._episode_frames[cam.key].append(image)

        self._episode_rows.append(row)

    def save_episode(self, parallel_encoding: bool = True) -> None:
        del parallel_encoding  # kept for call-site compatibility; see __init__ for what's actually deferred
        if not self._episode_rows:
            return

        episode_index = self._next_episode_index
        task = str(self._episode_rows[0].get("task", "task"))
        prompt = str(self._episode_rows[0].get("prompt", ""))
        task_index = self._ensure_task(task, prompt)

        episode_rows: list[dict[str, Any]] = []
        for frame_index, row in enumerate(self._episode_rows):
            item = dict(row)
            item["episode_index"] = episode_index
            item["frame_index"] = frame_index
            item["index"] = self._num_frames + frame_index
            item["task_index"] = task_index
            episode_rows.append(item)

        df = pd.DataFrame(episode_rows)
        parquet_path = self.data_dir / f"episode_{episode_index:06d}.parquet"
        df.to_parquet(parquet_path, index=False, compression="zstd")

        if self.cfg.use_videos:
            for cam in self.cfg.enabled_cameras:
                self._write_video(
                    camera_key=cam.key,
                    frames=self._episode_frames[cam.key],
                    width=cam.width,
                    height=cam.height,
                    episode_index=episode_index,
                )

        episodes_df = self._read_episodes()
        new_episode_row = pd.DataFrame(
            [
                {
                    "episode_index": episode_index,
                    "task": task,
                    "prompt": prompt,
                    "task_index": task_index,
                    "length": len(episode_rows),
                    "data_path": str(parquet_path.relative_to(self.root)),
                }
            ]
        )
        episodes_df = episodes_df[episodes_df["episode_index"] != episode_index]
        episodes_df = pd.concat([episodes_df, new_episode_row], ignore_index=True)
        episodes_df = episodes_df.sort_values("episode_index").reset_index(drop=True)
        episodes_df.to_parquet(self.episodes_path, index=False)

        self._num_episodes = len(episodes_df)
        self._num_frames += len(episode_rows)
        self._next_episode_index = episode_index + 1
        self.clear_episode_buffer()
        self._rebuild_info_json()
        self._enqueue_stats_rebuild()

    def clear_episode_buffer(self) -> None:
        self._episode_rows.clear()
        self._episode_frames = {cam.key: [] for cam in self.cfg.enabled_cameras}

    def finalize(self) -> None:
        # Drain any in-flight background stats rebuild first, then rebuild
        # once more directly so the final meta files are guaranteed fresh
        # regardless of what was still queued when finalize() was called.
        self.wait_for_pending_saves()
        self._rebuild_info_json()
        self._rebuild_stats_json()

    def push_to_hub(self, **kwargs: Any) -> None:
        del kwargs
        raise NotImplementedError("push_to_hub is not supported in the local-only v3 recorder")

    def _ensure_layout(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.episodes_path.parent.mkdir(parents=True, exist_ok=True)
        for cam in self.cfg.enabled_cameras:
            self.video_dir(cam.key).mkdir(parents=True, exist_ok=True)

    def _initialize_empty_meta(self) -> None:
        if not self.tasks_path.exists():
            pd.DataFrame(columns=["task_index", "task", "prompt"]).to_parquet(
                self.tasks_path, index=False
            )
        if not self.episodes_path.exists():
            pd.DataFrame(
                columns=[
                    "episode_index",
                    "task",
                    "prompt",
                    "task_index",
                    "length",
                    "data_path",
                ]
            ).to_parquet(self.episodes_path, index=False)

    def _compute_num_episodes(self) -> int:
        episodes = self._read_episodes()
        return len(episodes)

    def _compute_num_frames(self) -> int:
        episodes = self._read_episodes()
        if "length" not in episodes.columns or episodes.empty:
            return 0
        return int(episodes["length"].sum())

    def _compute_next_episode_index(self) -> int:
        episodes = self._read_episodes()
        if episodes.empty or "episode_index" not in episodes.columns:
            return 0
        return int(episodes["episode_index"].max()) + 1

    def _read_tasks(self) -> pd.DataFrame:
        if not self.tasks_path.exists():
            return pd.DataFrame(columns=["task_index", "task", "prompt"])
        tasks_df = pd.read_parquet(self.tasks_path)
        if "prompt" not in tasks_df.columns:
            tasks_df["prompt"] = ""
        return tasks_df

    def _read_episodes(self) -> pd.DataFrame:
        if not self.episodes_path.exists():
            return pd.DataFrame(
                columns=[
                    "episode_index",
                    "task",
                    "prompt",
                    "task_index",
                    "length",
                    "data_path",
                ]
            )
        episodes_df = pd.read_parquet(self.episodes_path)
        if "prompt" not in episodes_df.columns:
            episodes_df["prompt"] = ""
        return episodes_df

    def _ensure_task(self, task: str, prompt: str = "") -> int:
        tasks_df = self._read_tasks()
        if not tasks_df.empty and task in set(tasks_df["task"].astype(str)):
            match = tasks_df[tasks_df["task"].astype(str) == task].iloc[0]
            task_index = int(match["task_index"])
            if prompt:
                current_prompt = str(match.get("prompt", "") or "")
                if not current_prompt:
                    tasks_df.loc[tasks_df["task_index"] == task_index, "prompt"] = prompt
                    tasks_df = tasks_df.sort_values("task_index").reset_index(drop=True)
                    tasks_df.to_parquet(self.tasks_path, index=False)
            return task_index

        task_index = 0 if tasks_df.empty else int(tasks_df["task_index"].max()) + 1
        tasks_df = pd.concat(
            [
                tasks_df,
                pd.DataFrame(
                    [{"task_index": task_index, "task": task, "prompt": prompt}]
                ),
            ],
            ignore_index=True,
        )
        tasks_df = tasks_df.sort_values("task_index").reset_index(drop=True)
        tasks_df.to_parquet(self.tasks_path, index=False)
        return task_index

    def _write_video(
        self,
        camera_key: str,
        frames: list[np.ndarray],
        width: int,
        height: int,
        episode_index: int,
    ) -> None:
        codec_name = self._CODEC_MAP.get(self.cfg.vcodec, self.cfg.vcodec)
        video_path = self.video_dir(camera_key) / f"episode_{episode_index:06d}.mp4"
        container = av.open(str(video_path), mode="w")
        try:
            stream = container.add_stream(codec_name, rate=self.cfg.fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"

            for frame in frames:
                frame_rgb = self._resize_if_needed(frame, width=width, height=height)
                frame_av = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
                frame_av = frame_av.reformat(width=width, height=height, format="yuv420p")
                for packet in stream.encode(frame_av):
                    container.mux(packet)

            for packet in stream.encode():
                container.mux(packet)
        finally:
            container.close()

    def _rebuild_info_json(self) -> None:
        tasks_df = self._read_tasks()
        features = build_v3_features(
            feature_spec=self.cfg.feature_spec,
            cameras=self.cfg.enabled_cameras,
            use_videos=self.cfg.use_videos,
        )
        features.update(
            {
                "timestamp": {"dtype": "float32", "shape": [1], "names": None},
                "frame_index": {"dtype": "int64", "shape": [1], "names": None},
                "episode_index": {"dtype": "int64", "shape": [1], "names": None},
                "index": {"dtype": "int64", "shape": [1], "names": None},
                "task_index": {"dtype": "int64", "shape": [1], "names": None},
                "task": {"dtype": "string", "shape": [1], "names": None},
                "prompt": {"dtype": "string", "shape": [1], "names": None},
            }
        )
        info = {
            "codebase_version": "custom_v3_local",
            "repo_id": self.cfg.repo_id,
            "robot_type": self.cfg.robot_type,
            "fps": self.cfg.fps,
            "total_episodes": self._num_episodes,
            "total_frames": self._num_frames,
            "total_tasks": len(tasks_df),
            "use_videos": self.cfg.use_videos,
            "camera_keys": [cam.key for cam in self.cfg.enabled_cameras],
            "video_keys": [cam.key for cam in self.cfg.enabled_cameras],
            "features": features,
            "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
            "video_path": "videos/{video_key}/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.mp4",
            "splits": {"train": f"0:{self._num_episodes}"},
        }
        self.info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    def _rebuild_stats_json(self) -> None:
        numeric_columns = [
            "action",
            "observation.state",
            "observation.leader_state",
            "observation.follower_state",
        ]
        stats: dict[str, Any] = {}
        all_parquets = sorted(self.data_dir.glob("episode_*.parquet"))
        for column in numeric_columns:
            values: list[np.ndarray] = []
            for parquet in all_parquets:
                df = pd.read_parquet(parquet)
                if column not in df.columns:
                    continue
                for item in df[column].tolist():
                    values.append(np.asarray(item, dtype=np.float32).reshape(-1))
            try:
                stacked = np.stack(values, axis=0)
                stats[column] = {
                    "mean": stacked.mean(axis=0).tolist(),
                    "std": stacked.std(axis=0).tolist(),
                    "min": stacked.min(axis=0).tolist(),
                    "max": stacked.max(axis=0).tolist(),
                }
            except Exception as e:
                # Handle shape mismatches gracefully (e.g. mock runs mixed with real runs)
                pass
        self.stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    def _normalize_image(
        self,
        image: np.ndarray,
        hwc_shape: tuple[int, int, int],
    ) -> np.ndarray:
        if not isinstance(image, np.ndarray):
            raise TypeError("Camera frame must be numpy.ndarray")
        if image.ndim != 3 or image.shape[-1] != hwc_shape[2]:
            raise ValueError(
                f"Expected HWC image with channels={hwc_shape[2]}, got {image.shape}"
            )
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return self._resize_if_needed(image, width=hwc_shape[1], height=hwc_shape[0])

    def _resize_if_needed(self, image: np.ndarray, width: int, height: int) -> np.ndarray:
        if image.shape[1] == width and image.shape[0] == height:
            return image
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    def _serialize_extra(self, value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, (np.integer, np.floating)):
            return value.item()
        return value
