#!/usr/bin/env python3
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


def delete_episode(dataset_path, episode_id):
    root = Path(dataset_path)

    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset root is not a directory: {root}")

    ep = int(episode_id)
    ep_file = f"episode_{ep:06d}"

    print(f"\nDeleting episode: {ep_file}")

    # ---------------------------------------------------
    # Delete parquet data
    # ---------------------------------------------------
    data_file = root / "data" / "chunk-000" / f"{ep_file}.parquet"

    if data_file.exists():
        data_file.unlink()
        print(f"Deleted data file: {data_file}")
    else:
        print("Data parquet not found")

    # ---------------------------------------------------
    # Delete videos
    # ---------------------------------------------------
    deleted_video = False

    for video_file in root.glob(f"videos/*/chunk-000/{ep_file}.mp4"):
        video_file.unlink()
        print(f"Deleted video: {video_file}")
        deleted_video = True

    if not deleted_video:
        print("No video files found")

    # ---------------------------------------------------
    # Remove episode from episodes.parquet
    # ---------------------------------------------------
    episodes_path = (
        root
        / "meta"
        / "episodes"
        / "chunk-000"
        / "episodes.parquet"
    )

    if not episodes_path.exists():
        raise FileNotFoundError(
            f"Missing episodes metadata file: {episodes_path}"
        )

    df = pd.read_parquet(episodes_path)

    old_len = len(df)

    df = df[df["episode_index"] != ep].reset_index(drop=True)
    df = df.sort_values("episode_index").reset_index(drop=True)

    new_len = len(df)

    if old_len == new_len:
        print(f"Episode {ep} not found in metadata")
        raise ValueError(f"Episode {ep} not found in metadata")
    else:
        # Shift files and index to keep things perfectly sequential
        print("Resequencing remaining episodes to prevent gaps...")
        for new_idx, row in df.iterrows():
            old_idx = int(row["episode_index"])
            if old_idx == new_idx:
                continue
                
            # Rename parquet file
            old_parquet = root / "data" / "chunk-000" / f"episode_{old_idx:06d}.parquet"
            new_parquet = root / "data" / "chunk-000" / f"episode_{new_idx:06d}.parquet"
            if old_parquet.exists():
                if new_parquet.exists():
                    new_parquet.unlink()
                old_parquet.rename(new_parquet)
                
            # Rename video files
            for old_vid in root.glob(f"videos/*/chunk-000/episode_{old_idx:06d}.mp4"):
                new_vid = old_vid.parent / f"episode_{new_idx:06d}.mp4"
                if old_vid.exists():
                    if new_vid.exists():
                        new_vid.unlink()
                    old_vid.rename(new_vid)
                    
            # Update dataframe row
            df.at[new_idx, "episode_index"] = new_idx
            df.at[new_idx, "data_path"] = f"data/chunk-000/episode_{new_idx:06d}.parquet"

        df.to_parquet(episodes_path, index=False)
        print(f"Removed episode {ep} and packed gaps. Next episode index will be {len(df)}.")

    # ---------------------------------------------------
    # Rebuild info.json and stats.json
    # ---------------------------------------------------
    info_path = root / "meta" / "info.json"

    if not info_path.exists():
        raise FileNotFoundError(f"Missing info file: {info_path}")

    info = json.loads(info_path.read_text(encoding="utf-8"))

    features = info["features"]

    cfg = V3DatasetConfig(
        repo_id=info.get("repo_id", "local/bi_arm"),
        root=root,
        fps=int(info.get("fps", 10)),
        robot_type=info.get(
            "robot_type",
            "leader_follower_6dof_4camera"
        ),

        cameras=[
            CameraSpec(
                key=key,
                role="secondary",
                height=240,
                width=320,
            )
            for key in info.get("camera_keys", [])
        ],

        feature_spec=V3FeatureSpec(
            action_dim=features["action"]["shape"][0],
            follower_state_dim=features["observation.state"]["shape"][0],
            leader_state_dim=features["observation.leader_state"]["shape"][0],
        ),

        use_videos=bool(info.get("use_videos", True)),
        vcodec="h264",
        streaming_encoding=True,
    )

    print("\nRebuilding dataset metadata...")

    rec = V3DatasetRecorder.resume_existing(cfg)
    rec.finalize()

    new_info = json.loads(info_path.read_text(encoding="utf-8"))

    print("\nDone")
    print("Total episodes:", new_info["total_episodes"])
    print("Total frames:", new_info["total_frames"])


def main():
    parser = argparse.ArgumentParser(description="Delete a specific episode from the dataset.")

    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset root path"
    )

    parser.add_argument(
        "--episode",
        required=True,
        type=int,
        help="Episode number to delete"
    )

    args = parser.parse_args()

    try:
        delete_episode(args.dataset, args.episode)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
