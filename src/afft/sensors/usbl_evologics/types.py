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
    x: Forward offset from ship reference point in metres.
    y: Lateral offset in metres (positive starboard).
    z: Vertical offset in metres (positive down).
    phi: Roll in radians (positive: starboard down).
    theta: Pitch in radians (positive: bow up).
    psi: Yaw in radians (positive clockwise viewed from above).
    """

    x: float
    y: float
    z: float
    phi: float = 0.0
    theta: float = 0.0
    psi: float = 0.0

    @property
    def translation(self) -> NDArray[np.float64]:
        return np.array([self.x, self.y, self.z], dtype=np.float64)

    @property
    def rotation(self) -> Rotation:
        return Rotation.from_euler(
            "zyx", [self.psi, self.theta, self.phi], degrees=False
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
