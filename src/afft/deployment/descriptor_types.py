"""Data types describing a single ACFR deployment."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .types import DeploymentMetadata


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
    """

    model_config = ConfigDict(frozen=True)

    key: str
    message_topics: list[str] = Field(default_factory=list)
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None


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
    """

    model_config = ConfigDict(frozen=True)

    key: str
    message_topics: list[str] = Field(default_factory=list)
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None


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


class DeploymentPlatformSection(BaseModel):
    """
    The deployment platform's curated identity and its sensor roster.

    Filled entirely by enrichment from the assigned catalog profile: the
    system config's roster is a vehicle-scoped set of labels rather than a
    curated vocabulary, and it is kept as observed data on the system section
    instead. Poses are in the vehicle (SNAME) body frame.

    Attributes
    ----------
    identity: Curated platform identity; ``None`` until enrichment fills it.
    sensors: One entry per curated platform sensor; empty until enrichment
        fills it.
    """

    model_config = ConfigDict(frozen=True)

    identity: PlatformIdentity | None = None
    sensors: list[PlatformSensor] = Field(default_factory=list)


class DeploymentVesselSection(BaseModel):
    """
    The support vessel's curated identity and its sensor roster.

    Filled entirely by enrichment: the vessel is topside, so nothing in the
    deployment data names it. Poses are in the ship reference frame.

    Attributes
    ----------
    identity: Curated vessel identity; ``None`` until enrichment fills it.
    sensors: One entry per curated vessel sensor; empty until enrichment fills
        it.
    """

    model_config = ConfigDict(frozen=True)

    identity: VesselIdentity | None = None
    sensors: list[VesselSensor] = Field(default_factory=list)


class DeploymentSystemSection(BaseModel):
    """
    The deployment vehicle's identity and logging setup, from the SEABED
    system config.

    Attributes
    ----------
    vehicle_name: Vehicle name (e.g. ``"SEABED"``).
    vehicle_config: Vehicle configuration (e.g. ``"NORM_CFG"``).
    log_directory: On-vehicle log directory (e.g. ``"/files1/Log"``).
    logged_streams: Stream types written to disk (e.g. ``["SYSLOG", "RAW",
        "CTL", "AUV", "MSG", "RDI"]``).
    sensors: Sensor labels the config declares (e.g. ``["RDI", "VIS",
        "MP_INPUT"]``), kept as observed data. The labels are scoped to one
        vehicle configuration and the roster is not always complete, so it
        stands beside the curated ``platform.sensors`` rather than feeding it
        — its value is that the two can disagree.
    """

    model_config = ConfigDict(frozen=True)

    vehicle_name: str
    vehicle_config: str
    log_directory: str
    logged_streams: list[str]
    sensors: list[str] = Field(default_factory=list)


class DeploymentFileSection(BaseModel):
    """
    Flat inventory of a deployment's files, keyed by role.

    Each field is a role holding the matching paths relative to the deployment
    root, sorted. A role with no files is an empty list, so every deployment
    carries the full role vocabulary.

    Attributes
    ----------
    raw_messages: Raw telemetry logs.
    system_config: SEABED system config.
    localizer_config: SEABED localizer config.
    magvar_config: Magnetic variation config.
    mission_log: Mission log.
    camera_calibrations: Camera calibration files.
    camera_poses: Stereo pose estimates.
    usbl_logs: Topside USBL text logs.
    """

    model_config = ConfigDict(frozen=True)

    raw_messages: list[str] = Field(default_factory=list)
    system_config: list[str] = Field(default_factory=list)
    localizer_config: list[str] = Field(default_factory=list)
    magvar_config: list[str] = Field(default_factory=list)
    mission_log: list[str] = Field(default_factory=list)
    camera_calibrations: list[str] = Field(default_factory=list)
    camera_poses: list[str] = Field(default_factory=list)
    usbl_logs: list[str] = Field(default_factory=list)


class DeploymentTelemetrySection(BaseModel):
    """
    Message topics observed in the deployment's RAW AUV telemetry logs.

    Attributes
    ----------
    topics: Sorted unique message topic names observed across all RAW AUV log
        files (e.g. ``["GPS_RMC", "RDI", "VIS"]``).
    """

    model_config = ConfigDict(frozen=True)

    topics: list[str]


class DeploymentDescriptor(BaseModel):
    """
    Structured, human-readable description of a single ACFR deployment.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_datetime: Deployment datetime.
    metadata: Collected deployment metadata.
    files: Inventory of the deployment's files, keyed by role.
    telemetry: Message topics observed in the RAW AUV logs.
    platform: The platform's curated identity and its sensor roster; empty
        until enrichment fills it.
    system: The vehicle's identity, logging setup, and configured sensor
        labels.
    vessel: The support vessel's curated identity and its sensor roster; empty
        until enrichment fills it.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_datetime: datetime

    metadata: DeploymentMetadata
    files: DeploymentFileSection
    telemetry: DeploymentTelemetrySection
    platform: DeploymentPlatformSection
    system: DeploymentSystemSection

    vessel: DeploymentVesselSection = Field(
        default_factory=DeploymentVesselSection
    )
