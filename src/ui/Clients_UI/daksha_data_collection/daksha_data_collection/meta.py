from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class V3MetadataReader:
    """
    Convenience reader around the local-only v3-style metadata files.
    """

    def __init__(self, repo_id: str, root: Path) -> None:
        self.repo_id = repo_id
        self.root = Path(root)

    @property
    def info(self) -> dict[str, Any]:
        path = self.root / "meta" / "info.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @property
    def stats(self) -> dict[str, Any] | None:
        path = self.root / "meta" / "stats.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @property
    def tasks(self) -> pd.DataFrame:
        path = self.root / "meta" / "tasks.parquet"
        if not path.exists():
            return pd.DataFrame(columns=["task_index", "task"])
        return pd.read_parquet(path)

    @property
    def episodes(self) -> pd.DataFrame | None:
        path = self.root / "meta" / "episodes" / "chunk-000" / "episodes.parquet"
        if not path.exists():
            return None
        return pd.read_parquet(path)

    def summary(self) -> dict[str, Any]:
        info = self.info
        return {
            "repo_id": self.repo_id,
            "codebase_version": info.get("codebase_version"),
            "total_episodes": info.get("total_episodes", 0),
            "total_frames": info.get("total_frames", 0),
            "total_tasks": info.get("total_tasks", 0),
            "video_keys": list(info.get("video_keys", [])),
            "camera_keys": list(info.get("camera_keys", [])),
            "features": list(info.get("features", {}).keys()),
        }
