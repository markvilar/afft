"""Data types for AUV deployment configuration."""

from dataclasses import dataclass


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
    sensor_keys: Identifiers for sensors active during this deployment.
    """

    label: str
    ship_name: str
    date: str
    usbl_modem: TopsideUsblModemConfig
    sensor_keys: tuple[str, ...] = ()
