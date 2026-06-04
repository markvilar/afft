"""Configuration types for the Evologics S2C R 18/34 USBL processor."""

import numpy as np

from dataclasses import dataclass

from numpy.typing import NDArray
from scipy.spatial.transform import (
    RigidTransform,
    Rotation,
)


@dataclass(slots=True, frozen=True)
class EvologicsTransceiverExtrinsics:
    """
    Rigid-body extrinsics of the Evologics USBL transceiver in the ship body frame.

    The ship body frame has x pointing forward (bow), y pointing starboard,
    and z pointing down. Angles follow ZYX intrinsic Euler convention
    (yaw ψ, pitch θ, roll φ) with right-hand-positive rotations.

    Attributes
    ----------
    locx: Forward offset from ship reference point in metres.
    locy: Lateral offset in metres (positive starboard).
    locz: Vertical offset in metres (positive down).
    rotx: Roll in radians (positive: starboard down).
    roty: Pitch in radians (positive: bow up).
    rotz: Yaw in radians (positive clockwise viewed from above).
    """

    locx: float
    locy: float
    locz: float
    rotx: float = 0.0
    roty: float = 0.0
    rotz: float = 0.0

    @property
    def translation(self) -> NDArray[np.float64]:
        return np.array([self.locx, self.locy, self.locz], dtype=np.float64)

    @property
    def rotation(self) -> Rotation:
        return Rotation.from_euler(
            "zyx", [self.rotz, self.roty, self.rotx], degrees=False
        )

    @property
    def transform(self) -> RigidTransform:
        return RigidTransform.from_components(
            translation=self.translation,
            rotation=self.rotation,
        )


@dataclass(slots=True, frozen=True)
class EvologicsProcessingConfig:
    """
    Configuration for the Evologics USBL processing pipeline.

    Attributes
    ----------
    extrinsics: Transceiver extrinsics in the ship body frame. When None,
        only the USBL-Frame flip is applied (no rotation or translation).
    horizontal_position_std: 1σ horizontal position uncertainty in metres.
    depth_position_std: 1σ depth uncertainty in metres.
    """

    extrinsics: EvologicsTransceiverExtrinsics | None = None
    horizontal_position_std: float = 15.8
    depth_position_std: float = 5.0
