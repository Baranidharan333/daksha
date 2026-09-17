from __future__ import annotations

from typing import Any

try:
    from .config import CameraSpec, V3FeatureSpec
except ImportError:
    from config import CameraSpec, V3FeatureSpec


def build_v3_features(
    feature_spec: V3FeatureSpec,
    cameras: list[CameraSpec],
    use_videos: bool = True,
) -> dict[str, dict[str, Any]]:
    """
    Build a local v3-style feature dictionary.
    Default bookkeeping fields (timestamp, frame_index, episode_index, index, task_index) are added by the local recorder metadata writer.
    """
    def get_names(dim: int, prefix: str) -> list[str]:
        if feature_spec.joint_names and len(feature_spec.joint_names) == dim:
            return list(feature_spec.joint_names)
        return [f"{prefix}_{i+1}" for i in range(dim)]

    features: dict[str, dict[str, Any]] = {
        "action": {
            "dtype": "float32",
            "shape": (feature_spec.action_dim,),
            "names": get_names(feature_spec.action_dim, "joint"),
        },
        "observation.state": {
            "dtype": "float32",
            "shape": (feature_spec.follower_state_dim,),
            "names": get_names(feature_spec.follower_state_dim, "follower_joint"),
        },
        "observation.leader_state": {
            "dtype": "float32",
            "shape": (feature_spec.leader_state_dim,),
            "names": get_names(feature_spec.leader_state_dim, "leader_joint"),
        },
    }
    if feature_spec.include_follower_state_duplicate:
        features["observation.follower_state"] = {
            "dtype": "float32",
            "shape": (feature_spec.follower_state_dim,),
            "names": get_names(feature_spec.follower_state_dim, "follower_joint"),
        }


    image_dtype = "video" if use_videos else "image"
    for cam in cameras:
        if not cam.enabled:
            continue
        features[cam.key] = {
            "dtype": image_dtype,
            "shape": cam.hwc_shape,
            "names": ["height", "width", "channels"],
        }
    return features

