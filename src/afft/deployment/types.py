"""Data types for AUV deployment configuration and metadata."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from .common_types import DeploymentMetadata, validate_temporal_range


class UsblUncertaintyProfile(BaseModel):
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

    model_config = ConfigDict(frozen=True)

    horizontal_position_std: float
    slant_range_std: float
    bearing_std: float
    ship_x_std: float
    ship_y_std: float
    ship_z_std: float
    ship_heading_std: float
    ship_roll_std: float
    ship_pitch_std: float


class TopsideUsblModemConfig(BaseModel):
    """
    Position and orientation of the USBL transceiver in the ship reference frame.

    Attributes
    ----------
    locx: X position in metres.
    locy: Y position in metres.
    locz: Z position in metres.
    rotx: Roll angle in radians.
    roty: Pitch angle in radians.
    rotz: Yaw angle in radians.
    comment: Optional note about the calibration.
    """

    model_config = ConfigDict(frozen=True)

    locx: float
    locy: float
    locz: float
    rotx: float
    roty: float
    rotz: float
    comment: str = ""


class DeploymentConfig(BaseModel):
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

    model_config = ConfigDict(frozen=True)

    label: str
    ship_name: str
    date: str
    usbl_modem: TopsideUsblModemConfig
    usbl_uncertainty: UsblUncertaintyProfile
    sensor_keys: tuple[str, ...] = ()


class DeploymentInfo(BaseModel):
    """
    Core identity fields for a single AUV deployment.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_start_datetime: Start datetime of the deployment.
    deployment_end_datetime: End datetime of the deployment; ``None`` when the
        deployment covers its own full temporal range and no end was recorded.
    deployment_platform: Squidle+ platform name for this deployment.
    metadata: Collected deployment metadata.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_start_datetime: datetime
    deployment_end_datetime: datetime | None = None
    deployment_platform: str
    metadata: DeploymentMetadata

    @model_validator(mode="after")
    def _check_temporal_range(self) -> Self:
        validate_temporal_range(
            self.deployment_start_datetime, self.deployment_end_datetime
        )
        return self
