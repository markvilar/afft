"""Data types for AUV deployment configuration."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class UsblUncertaintyProfile:
    """
    Deployment-calibrated USBL uncertainty profile (1σ standard deviations).

    Attributes
    ----------
    horizontal_position_std: Horizontal position uncertainty in metres (isotropic).
    slant_range_std: Slant-range measurement uncertainty in metres.
    bearing_std: Bearing measurement uncertainty in radians.
    ship_x_std: Ship GPS x uncertainty in metres.
    ship_y_std: Ship GPS y uncertainty in metres.
    ship_z_std: Ship GPS z uncertainty in metres.
    ship_heading_std: Ship heading uncertainty in radians.
    ship_roll_std: Ship roll uncertainty in radians.
    ship_pitch_std: Ship pitch uncertainty in radians.
    """

    horizontal_position_std: float
    slant_range_std: float
    bearing_std: float
    ship_x_std: float
    ship_y_std: float
    ship_z_std: float
    ship_heading_std: float
    ship_roll_std: float
    ship_pitch_std: float


@dataclass(slots=True, frozen=True)
class TopsideUsblModemConfig:
    """
    Position and orientation of the USBL transceiver in the ship reference frame.

    Attributes
    ----------
    x: X position in metres.
    y: Y position in metres.
    z: Z position in metres.
    phi: Roll angle in radians.
    theta: Pitch angle in radians.
    psi: Yaw angle in radians.
    comment: Optional note about the calibration.
    """

    x: float
    y: float
    z: float
    phi: float
    theta: float
    psi: float
    comment: str = ""


@dataclass(slots=True, frozen=True)
class DeploymentConfig:
    """
    Configuration for a single AUV deployment.

    Attributes
    ----------
    label: Unique deployment identifier.
    ship_name: Name of the support vessel.
    date: Deployment date string (YYYYMM).
    usbl_modem: Topside USBL transceiver extrinsics.
    usbl_uncertainty: Deployment-calibrated USBL uncertainty profile.
    sensor_keys: Identifiers for sensors active during this deployment.
    """

    label: str
    ship_name: str
    date: str
    usbl_modem: TopsideUsblModemConfig
    usbl_uncertainty: UsblUncertaintyProfile
    sensor_keys: tuple[str, ...] = ()
