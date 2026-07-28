"""Data types for AUV deployment configuration and metadata."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class DeploymentMetadata(BaseModel):
    """
    Collected metadata for a single AUV deployment.

    Attributes
    ----------
    acfr_deployment_label: ACFR mission file stem.
    acfr_campaign_label: ACFR campaign directory name.
    acfr_platform_label: ACFR platform name.
    origin_latitude: Deployment origin latitude in decimal degrees.
    origin_longitude: Deployment origin longitude in decimal degrees.
    magnetic_variation: Magnetic variation at the origin in degrees.
    message_topics: Sorted unique message topic names from the RAW AUV logs.
    renav_labels: Sorted renav run labels from the camera poses directory.
    camera_calibration_files: Sorted unique camera calibration filenames.
    """

    model_config = ConfigDict(frozen=True)

    acfr_deployment_label: str
    acfr_campaign_label: str
    acfr_platform_label: str
    origin_latitude: float
    origin_longitude: float
    magnetic_variation: float
    message_topics: list[str]
    renav_labels: list[str]
    camera_calibration_files: list[str]


class DeploymentInfo(BaseModel):
    """
    Core identity fields for a single AUV deployment.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_datetime: Deployment datetime.
    deployment_platform: Squidle+ platform name for this deployment.
    metadata: Collected deployment metadata.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_datetime: datetime
    deployment_platform: str
    metadata: DeploymentMetadata
