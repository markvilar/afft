"""Data types shared across deployment descriptor and deployment bundle representations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def validate_temporal_range(
    start: datetime,
    end: datetime | None,
) -> None:
    """
    Validate a deployment's temporal range.

    An absent end is valid: it means the deployment covers its own full
    temporal range and no end was recorded. A present end must be strictly
    after the start, since a deployment spanning no time is not a deployment.

    Arguments
    ---------
    start: Start datetime of the deployment.
    end: End datetime of the deployment, or ``None``.

    Raises
    ------
    ValueError: If `end` is given and is not strictly after `start`.
    """
    if end is not None and end <= start:
        raise ValueError(
            f"deployment end datetime must be after its start: "
            f"{end.isoformat()} <= {start.isoformat()}"
        )


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
    """

    model_config = ConfigDict(frozen=True)

    acfr_deployment_label: str
    acfr_campaign_label: str
    acfr_platform_label: str
    origin_latitude: float
    origin_longitude: float
    magnetic_variation: float


class SensorIdentity(BaseModel):
    """
    Curated identity of a sensor, filled by enrichment from the deployment
    catalog. Vendor and product are empty where the hardware has no published
    record.

    Attributes
    ----------
    label: Human-readable sensor name.
    vendor: Manufacturer (e.g. ``"Teledyne RDI"``).
    product: Product name (e.g. ``"Work Horse Navigator"``).
    type: Sensor type (e.g. ``"dvl"``).
    """

    model_config = ConfigDict(frozen=True)

    label: str
    vendor: str
    product: str
    type: str


class SensorExtrinsics(BaseModel):
    """
    A sensor's mounting pose, in the reference frame of the body it is mounted
    on — stated by the descriptor section the sensor lives in. Filled by
    enrichment.

    Attributes
    ----------
    locx: X translation in metres.
    locy: Y translation in metres.
    locz: Z translation in metres.
    rotx: Roll angle in radians.
    roty: Pitch angle in radians.
    rotz: Yaw angle in radians.
    """

    model_config = ConfigDict(frozen=True)

    locx: float
    locy: float
    locz: float
    rotx: float
    roty: float
    rotz: float


class SensorCalibration(BaseModel):
    """
    A sensor's calibration. Filled during bundle building from parsed
    calibration files, not by enrichment — unlike identity and extrinsics,
    it has no catalog source.

    Attributes
    ----------
    calibration_type: Discriminates which calibration model ``parameters``
        follows, e.g. ``"pinhole"``, ``"fisheye"``.
    parameters: Named calibration values for that model.
    """

    model_config = ConfigDict(frozen=True)

    calibration_type: str
    parameters: dict[str, float]


class PlatformSensor(BaseModel):
    """
    A sensor mounted on the deployment's platform. The whole roster is curated
    — enrichment writes it from the assigned catalog profile — so a platform
    section either has no sensors at all or has them fully identified.

    Attributes
    ----------
    key: Curated sensor identifier (e.g. ``"dvl_teledyne_navigator"``); the
        catalog lookup key.
    message_topics: RAW telemetry topics the sensor emits, carried from the
        catalog so the descriptor states the mapping a build used. Empty where
        the sensor emits no topic.
    identity: Curated sensor metadata; ``None`` only on a roster no enrichment
        wrote.
    extrinsics: Mounting pose in the vehicle (SNAME) body frame; ``None``
        where the sensor has no surveyed pose.
    calibration: Camera calibration parameters; ``None`` until bundle
        building resolves it from parsed calibration files.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    message_topics: list[str] = Field(default_factory=list)
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None
    calibration: SensorCalibration | None = None


class VesselSensor(BaseModel):
    """
    A sensor mounted on the deployment's support vessel, its pose in the ship
    reference frame rather than the vehicle (SNAME) body frame.

    Attributes
    ----------
    key: Curated sensor identifier (e.g. ``"usbl_linkquest_transceiver"``);
        the catalog lookup key.
    message_topics: RAW telemetry topics the sensor emits; empty for the
        topside sensors, whose data arrives through a file role instead.
    identity: Curated sensor metadata; ``None`` only on a roster no enrichment
        wrote.
    extrinsics: Mounting pose in the ship reference frame; ``None`` where the
        sensor has no surveyed pose.
    calibration: Camera calibration parameters; ``None`` until bundle
        building resolves it from parsed calibration files.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    message_topics: list[str] = Field(default_factory=list)
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None
    calibration: SensorCalibration | None = None


class PlatformIdentity(BaseModel):
    """
    Curated identity of the deployment's platform, filled by enrichment. Only
    ``platform_class`` has a counterpart in the deployment data files, as
    ``system.vehicle_name``.

    Attributes
    ----------
    platform_label: Human-readable platform name (e.g. ``"AUV Sirius"``).
    platform_class: Vehicle class / system config vehicle name (e.g.
        ``"SEABED"``).
    platform_operator: Operating institution (e.g. ``"ACFR"``).
    """

    model_config = ConfigDict(frozen=True)

    platform_label: str
    platform_class: str
    platform_operator: str


class VesselIdentity(BaseModel):
    """
    Curated identity of the deployment's support vessel.

    Attributes
    ----------
    vessel_name: Support vessel name (e.g. ``"RV Linnaeus"``).
    """

    model_config = ConfigDict(frozen=True)

    vessel_name: str
