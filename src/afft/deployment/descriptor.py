"""Data types describing a single ACFR deployment."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .types import DeploymentMetadata


class SensorIdentity(BaseModel):
    """
    Curated identity of a sensor — vendor, product, and label.

    Populated by a later enrichment process; the fields are finalized there.
    Expected to hold a human-friendly label (e.g. ``"Teledyne RDI Workhorse
    Navigator 1200"``) plus vendor and product metadata.
    """

    model_config = ConfigDict(frozen=True)


class SensorExtrinsics(BaseModel):
    """
    A sensor's mounting pose, in the reference frame of the body it is mounted
    on — stated by the descriptor section the sensor lives in.

    Populated by a later enrichment process that reconciles the localizer
    config's pose families with the system-config-derived sensor roster via a
    curated alias table (e.g. localizer ``DVL`` -> syscfg ``RDI``).

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
    A sensor mounted on the deployment's platform.

    Attributes
    ----------
    key: Terse sensor identifier and RAW AUV message topic prefix (e.g.
        ``"RDI"``); also the enrichment catalog lookup key.
    identity: Curated sensor metadata; ``None`` until enrichment fills it.
    extrinsics: Sensor mounting pose in the vehicle (SNAME) body frame;
        ``None`` until enrichment fills it from the localizer config.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None


class VesselSensor(BaseModel):
    """
    A sensor mounted on the deployment's support vessel.

    Distinct from ``PlatformSensor`` because its ``extrinsics`` are expressed
    in the ship reference frame rather than the vehicle (SNAME) body frame.

    Attributes
    ----------
    key: Terse sensor identifier (e.g. ``"USBL"``); also the enrichment catalog
        lookup key.
    identity: Curated sensor metadata; ``None`` until enrichment fills it.
    extrinsics: Sensor mounting pose in the ship reference frame; ``None``
        until enrichment fills it from the curated USBL extrinsics catalog.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    identity: SensorIdentity | None = None
    extrinsics: SensorExtrinsics | None = None


class PlatformIdentity(BaseModel):
    """
    Curated identity of the deployment's platform.

    Populated by a later enrichment process from a curated platform catalog.
    Not derivable from the deployment data files — only ``platform_class`` has
    a counterpart there (``system.vehicle_name``), which is the catalog's
    natural lookup key.

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

    The roster is derived from the SEABED system config at describe time;
    ``identity`` and the sensors' curated slots are filled by enrichment.

    Sensor extrinsics in this section are expressed in the vehicle (SNAME)
    body frame, unlike ``DeploymentVesselSection``, whose poses are in the
    ship reference frame.

    Attributes
    ----------
    identity: Curated platform identity; ``None`` until enrichment fills it.
    sensors: One entry per configured platform sensor.
    """

    model_config = ConfigDict(frozen=True)

    identity: PlatformIdentity | None = None
    sensors: list[PlatformSensor] = Field(default_factory=list)


class DeploymentVesselSection(BaseModel):
    """
    The support vessel's curated identity and its sensor roster.

    Populated by a later enrichment process from the curated USBL extrinsics
    catalog. Not derivable from the deployment data files: the support vessel
    is topside, and nothing in the system config names it.

    Attributes
    ----------
    identity: Curated vessel identity; ``None`` until enrichment fills it.
    sensors: One entry per curated vessel sensor (USBL transceiver, ship GPS,
        ship attitude sensor); empty until enrichment fills it.
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
    """

    model_config = ConfigDict(frozen=True)

    vehicle_name: str
    vehicle_config: str
    log_directory: str
    logged_streams: list[str]


class DeploymentFileSection(BaseModel):
    """
    Flat inventory of a deployment's files, keyed by role.

    Each field is a role; its value is the matching file paths relative to the
    deployment root, sorted. A role with no matching files is an empty list, so
    every deployment carries the full role vocabulary.

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
    platform: The platform's curated identity and its sensor roster.
    system: The vehicle's identity and logging setup.
    vessel: The support vessel's curated identity and its sensor roster;
        ``None`` until enrichment fills it.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_datetime: datetime

    metadata: DeploymentMetadata
    files: DeploymentFileSection
    telemetry: DeploymentTelemetrySection
    platform: DeploymentPlatformSection
    system: DeploymentSystemSection

    vessel: DeploymentVesselSection | None = None
