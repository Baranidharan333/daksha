#!/usr/bin/env python3
"""Delete an episode from a local v3 dataset and keep every file consistent.

Used by both the web UI (/api/dataset/delete-episode) and the CLI, so the two
always behave the same:

  1. remove the episode's data parquet + one mp4 per camera
  2. drop it from meta/episodes/.../episodes.parquet
  3. repair_dataset(): renumber the remaining episodes 0..N-1 (files and the
     episode_index / frame_index / index columns inside them), remove orphan
     files, then rebuild meta/info.json, meta/stats.json (and tasks.json if
     the dataset has one)

`repair_dataset()` can also be run on its own (--repair) to fix a dataset
that already has holes in its numbering or a broken global frame index.
"""
from pathlib import Path
import json
import argparse
import sys
import pandas as pd

try:
    from daksha_data_collection.config import (
        CameraSpec,
        V3DatasetConfig,
        V3FeatureSpec,
    )
    from daksha_data_collection.recorder import V3DatasetRecorder
except ImportError:
    try:
        from .config import (
            CameraSpec,
            V3DatasetConfig,
            V3FeatureSpec,
        )
        from .recorder import V3DatasetRecorder
    except ImportError:
        from config import (
            CameraSpec,
            V3DatasetConfig,
            V3FeatureSpec,
        )
        from recorder import V3DatasetRecorder


def _paths(root: Path):
    data_dir = root / "data" / "chunk-000"
    episodes_path = root / "meta" / "episodes" / "chunk-000" / "episodes.parquet"
    info_path = root / "meta" / "info.json"
    return data_dir, episodes_path, info_path


def _data_file(root: Path, idx: int) -> Path:
    return root / "data" / "chunk-000" / f"episode_{idx:06d}.parquet"


def _video_cam_dirs(root: Path) -> list[Path]:
    # Every camera directory under videos/ is expected to hold one file per
    # tracked episode. A camera missing a file for just one episode is
    # corruption, not a config difference.
    videos_root = root / "videos"
    if not videos_root.exists():
        return []
    return [d / "chunk-000" for d in sorted(videos_root.iterdir()) if d.is_dir()]


def _load_info(root: Path) -> dict:
    _, _, info_path = _paths(root)
    if not info_path.exists():
        raise FileNotFoundError(f"Missing info file: {info_path}")
    return json.loads(info_path.read_text(encoding="utf-8"))


def _check_root(root: Path) -> None:
    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset root is not a directory: {root}")


def delete_episode(dataset_path, episode_id):
    root = Path(dataset_path)
    _check_root(root)
    data_dir, episodes_path, _ = _paths(root)
    if not episodes_path.exists():
        raise FileNotFoundError(f"Missing episodes metadata file: {episodes_path}")
    _load_info(root)  # fail before touching anything if meta is unusable

    ep = int(episode_id)
    df = pd.read_parquet(episodes_path)
    if ep not in set(df["episode_index"].astype(int)):
        raise ValueError(f"Episode {ep} not found in metadata")

    print(f"\nDeleting episode: episode_{ep:06d}")

    # Check the files every *other* episode needs before deleting anything,
    # so a dataset that is already broken fails clean with nothing touched.
    remaining = df[df["episode_index"].astype(int) != ep]
    _require_episode_files(root, remaining["episode_index"].astype(int).tolist())

    data_file = _data_file(root, ep)
    if data_file.exists():
        data_file.unlink()
        print(f"Deleted data file: {data_file}")
    for cam_dir in _video_cam_dirs(root):
        vid = cam_dir / f"episode_{ep:06d}.mp4"
        if vid.exists():
            vid.unlink()
            print(f"Deleted video: {vid}")

    remaining.to_parquet(episodes_path, index=False)
    return repair_dataset(root)


def _require_episode_files(root: Path, indices: list[int]) -> None:
    cam_dirs = _video_cam_dirs(root)
    missing = []
    for idx in indices:
        if not _data_file(root, idx).exists():
            missing.append(str(_data_file(root, idx)))
        for cam_dir in cam_dirs:
            vid = cam_dir / f"episode_{idx:06d}.mp4"
            if not vid.exists():
                missing.append(str(vid))
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} file(s) listed in episodes.parquet are missing "
            f"(first: {missing[0]}). The dataset is already inconsistent; "
            "restore these files before deleting episodes."
        )


def repair_dataset(dataset_path):
    """Renumber episodes to 0..N-1, fix embedded indices, drop orphan files
    and rebuild info/stats. Safe to run on an already-consistent dataset."""
    root = Path(dataset_path)
    _check_root(root)
    data_dir, episodes_path, _ = _paths(root)
    info = _load_info(root)

    df = pd.read_parquet(episodes_path)
    df = df.sort_values("episode_index").reset_index(drop=True)
    _require_episode_files(root, df["episode_index"].astype(int).tolist())
    cam_dirs = _video_cam_dirs(root)

    # Renumber. Indices only ever move down and are processed in ascending
    # order, so the target slot is always already free.
    shifts = [
        (int(row["episode_index"]), new_idx)
        for new_idx, row in df.iterrows()
        if int(row["episode_index"]) != new_idx
    ]
    if shifts:
        print(f"Renumbering {len(shifts)} episode(s) to close gaps...")
    for old_idx, new_idx in shifts:
        _data_file(root, old_idx).rename(_data_file(root, new_idx))
        for cam_dir in cam_dirs:
            (cam_dir / f"episode_{old_idx:06d}.mp4").rename(cam_dir / f"episode_{new_idx:06d}.mp4")
    df["episode_index"] = range(len(df))
    df["data_path"] = [f"data/chunk-000/episode_{i:06d}.parquet" for i in range(len(df))]

    # Orphans: any episode file not tracked by episodes.parquet. Left behind
    # they get swept into stats.json (the stats rebuild globs data/).
    valid_count = len(df)
    for stray in sorted(data_dir.glob("episode_*.parquet")):
        if int(stray.stem.split("_")[1]) >= valid_count:
            stray.unlink()
            print(f"Removed orphaned data file: {stray}")
    for cam_dir in cam_dirs:
        for stray in sorted(cam_dir.glob("episode_*.mp4")):
            if int(stray.stem.split("_")[1]) >= valid_count:
                stray.unlink()
                print(f"Removed orphaned video file: {stray}")

    # Embedded columns: episode_index must match the filename, frame_index
    # restarts per episode, and the global `index` is contiguous across the
    # dataset. Only files that are actually wrong get rewritten.
    fixed = 0
    global_frame = 0
    lengths = []
    for idx in range(len(df)):
        path = _data_file(root, idx)
        ep_df = pd.read_parquet(path)
        n = len(ep_df)
        want_ep = [idx] * n
        want_frame = list(range(n))
        want_index = list(range(global_frame, global_frame + n))
        if (
            ep_df.get("episode_index", pd.Series(dtype=int)).tolist() != want_ep
            or ep_df.get("frame_index", pd.Series(dtype=int)).tolist() != want_frame
            or ep_df.get("index", pd.Series(dtype=int)).tolist() != want_index
        ):
            ep_df["episode_index"] = want_ep
            ep_df["frame_index"] = want_frame
            ep_df["index"] = want_index
            ep_df.to_parquet(path, index=False, compression="zstd")
            fixed += 1
        lengths.append(n)
        global_frame += n
    if fixed:
        print(f"Repaired embedded indices in {fixed} data file(s)")
    df["length"] = lengths
    df.to_parquet(episodes_path, index=False)

    _rebuild_meta(root, info)

    new_info = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))
    print("\nDone")
    print("Total episodes:", new_info["total_episodes"])
    print("Total frames:", new_info["total_frames"])
    return new_info


def _rebuild_meta(root: Path, info: dict) -> None:
    """Rebuild info.json/stats.json with the recorder's own writers, using the
    dataset's existing feature shapes rather than guessed defaults."""
    features = info["features"]
    cameras = []
    for key in info.get("camera_keys", []):
        shape = features.get(key, {}).get("shape", [240, 320, 3])
        cameras.append(CameraSpec(key=key, role="secondary",
                                  height=int(shape[0]), width=int(shape[1]),
                                  channels=int(shape[2]) if len(shape) > 2 else 3))

    cfg = V3DatasetConfig(
        repo_id=info.get("repo_id", f"local/{root.name}"),
        root=root,
        fps=int(info.get("fps", 30)),
        robot_type=info.get("robot_type", "bimanual_leader_follower"),
        cameras=cameras,
        feature_spec=V3FeatureSpec(
            action_dim=features["action"]["shape"][0],
            follower_state_dim=features["observation.state"]["shape"][0],
            leader_state_dim=features["observation.leader_state"]["shape"][0],
            include_follower_state_duplicate="observation.follower_state" in features,
        ),
        use_videos=bool(info.get("use_videos", True)),
        vcodec="h264",
        streaming_encoding=True,
    )

    print("\nRebuilding dataset metadata (info.json, stats.json)...")
    rec = V3DatasetRecorder.resume_existing(cfg)
    rec.finalize()

    # Some datasets carry a legacy meta/tasks.json copy -- keep it in sync.
    tasks_json = root / "meta" / "tasks.json"
    tasks_parquet = root / "meta" / "tasks.parquet"
    if tasks_json.exists() and tasks_parquet.exists():
        tdf = pd.read_parquet(tasks_parquet).sort_values("task_index")
        tasks_json.write_text(tdf.to_json(orient="records", indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Delete an episode (or repair) a local v3 dataset.")
    parser.add_argument("--dataset", required=True, help="Dataset root path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", type=int, help="Episode index to delete (0-based)")
    group.add_argument("--repair", action="store_true",
                       help="Only renumber/fix indices/remove orphans and rebuild meta")
    args = parser.parse_args()

    try:
        if args.repair:
            repair_dataset(args.dataset)
        else:
            delete_episode(args.dataset, args.episode)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
