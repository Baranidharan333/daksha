from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

try:
    from .config import CameraSpec
except ImportError:
    from config import CameraSpec


class BaseCameraSource(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_rgb(self) -> Optional[np.ndarray]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


@dataclass
class OpenCVCameraSource(BaseCameraSource):
    index: int
    spec: CameraSpec

    def __post_init__(self) -> None:
        self._cap = cv2.VideoCapture(self.index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.spec.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.spec.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.spec.fps)

    @property
    def key(self) -> str:
        return self.spec.key

    def read_rgb(self) -> Optional[np.ndarray]:
        ok, frame_bgr = self._cap.read()
        if not ok:
            return None
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    def close(self) -> None:
        self._cap.release()

