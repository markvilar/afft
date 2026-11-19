"""Data types for Renav camera sensor calibrations (``*.calib``)."""

from __future__ import annotations

from enum import Enum
from typing import Self

import numpy as np

from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, model_validator
from scipy.spatial.transform import RigidTransform, Rotation


type Vec3 = tuple[float, float, float]
type Mat3 = tuple[Vec3, Vec3, Vec3]


class CameraCalibration(BaseModel):
    """
    Intrinsic calibration of a single camera, in OpenCV convention.

    Attributes
    ----------
    image_width: Image width, in pixels, at which the camera was calibrated.
    image_height: Image height, in pixels, at which the camera was calibrated.
    fx: Focal length along the x axis, in pixels.
    fy: Focal length along the y axis, in pixels.
    cx: Optical center x coordinate, in pixels.
    cy: Optical center y coordinate, in pixels.
    k1: First radial distortion coefficient.
    k2: Second radial distortion coefficient.
    k3: Third radial distortion coefficient.
    p1: First tangential distortion coefficient.
    p2: Second tangential distortion coefficient.
    """

    model_config = ConfigDict(frozen=True)

    image_width: int
    image_height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float
    k2: float
    k3: float
    p1: float
    p2: float

    @property
    def camera_matrix(self) -> NDArray[np.float64]:
        """3x3 intrinsic camera matrix K."""
        return np.array(
            [
                [self.fx, 0.0, self.cx],
                [0.0, self.fy, self.cy],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

    @property
    def distortion_coefficients(self) -> NDArray[np.float64]:
        """Distortion vector (k1, k2, p1, p2, k3), in OpenCV order."""
        return np.array(
            [self.k1, self.k2, self.p1, self.p2, self.k3],
            dtype=np.float64,
        )


class CameraSensor(BaseModel):
    """
    A camera sensor: intrinsic calibration plus extrinsics relative to a master.

    Attributes
    ----------
    key: Stable identifier for the sensor.
    label: Human-readable name.
    image_width: Image width in pixels.
    image_height: Image height in pixels.
    color_bands: Color bands captured by the sensor (MONO or RGB).
    calibration: Intrinsic calibration.
    location_in_master: Translation relative to the master (tx, ty, tz); zero
        when this sensor is the master.
    rotation_in_master: 3x3 rotation matrix relative to the master, row-major;
        identity when this sensor is the master.
    master_camera_sensor: The master sensor in a multi-camera setup, or None
        when this sensor is the master.
    """

    class ColorBands(Enum):
        """Color bands captured by a camera sensor."""

        MONO = "mono"
        RGB = "rgb"

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    image_width: int
    image_height: int
    color_bands: CameraSensor.ColorBands = ColorBands.RGB
    calibration: CameraCalibration
    location_in_master: Vec3
    rotation_in_master: Mat3
    master_camera_sensor: CameraSensor | None = None

    @property
    def master(self) -> CameraSensor | None:
        """The master sensor, or None when this sensor is the master."""
        return self.master_camera_sensor

    @property
    def is_master(self) -> bool:
        """Whether this sensor is a master (has no master of its own)."""
        return self.master_camera_sensor is None

    @property
    def is_slave(self) -> bool:
        """Whether this sensor is a slave (has a master)."""
        return self.master_camera_sensor is not None

    @property
    def rotation_matrix(self) -> NDArray[np.float64]:
        """3x3 rotation matrix relative to the master."""
        return np.array(self.rotation_in_master, dtype=np.float64)

    @property
    def transform_to_master(self) -> RigidTransform:
        """Rigid transform from this sensor's frame into the master's frame."""
        return RigidTransform.from_components(
            translation=np.array(self.location_in_master, dtype=np.float64),
            rotation=Rotation.from_matrix(self.rotation_matrix),
        )


class StereoCameraRig(BaseModel):
    """
    A stereo camera rig: a master sensor and a slave sensor posed to it.

    Attributes
    ----------
    master: The reference (master) camera sensor.
    slave: The slave camera sensor, posed relative to the master.
    """

    model_config = ConfigDict(frozen=True)

    master: CameraSensor
    slave: CameraSensor

    @model_validator(mode="after")
    def check_slave_master(self) -> Self:
        """Validate that the slave's master is the rig's master."""
        if self.slave.master_camera_sensor != self.master:
            raise ValueError(
                "slave's master_camera_sensor must be the rig's master"
            )
        return self


CameraSensor.model_rebuild()
