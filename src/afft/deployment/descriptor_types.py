"""Data types describing a single ACFR deployment."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common_types import (
    DeploymentMetadata,
    PlatformIdentity,
    PlatformSensor,
    VesselIdentity,
    VesselSensor,
    validate_temporal_range,
)


class PlatformDescriptorSection(BaseModel):
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


class VesselDescriptorSection(BaseModel):
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


class SystemDescriptorSection(BaseModel):
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


class SquidleDescriptorSection(BaseModel):
    """
    Curated Squidle+ identity for the deployment, filled by
    ``deployment enrich-squidle``.

    Every field is ``None`` until a match is resolved; ``deployment_id``/
    ``deployment_key``/``deployment_name`` can be filled even when the
    campaign/platform follow-up lookups fail. Field names follow Squidle+'s
    own vocabulary (``name``/``key``) rather than ACFR's ``_label``
    convention used elsewhere on the descriptor.

    Attributes
    ----------
    deployment_id: Squidle+ deployment id.
    deployment_key: Squidle+ deployment key.
    deployment_name: Squidle+ deployment name.
    campaign_id: Squidle+ campaign id.
    campaign_key: Squidle+ campaign key.
    campaign_name: Squidle+ campaign name.
    platform_id: Squidle+ platform id.
    platform_key: Squidle+ platform key.
    platform_name: Squidle+ platform name.
    """

    model_config = ConfigDict(frozen=True)

    deployment_id: int | None = None
    deployment_key: str | None = None
    deployment_name: str | None = None
    campaign_id: int | None = None
    campaign_key: str | None = None
    campaign_name: str | None = None
    platform_id: int | None = None
    platform_key: str | None = None
    platform_name: str | None = None


class FileDescriptorSection(BaseModel):
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


class TelemetryDescriptorSection(BaseModel):
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
    deployment_start_datetime: Start datetime of the deployment.
    deployment_end_datetime: End datetime of the deployment; ``None`` when the
        deployment covers its own full temporal range and no end was recorded.
    metadata: Collected deployment metadata.
    files: Inventory of the deployment's files, keyed by role.
    telemetry: Message topics observed in the RAW AUV logs.
    platform: The platform's curated identity and its sensor roster; empty
        until enrichment fills it.
    system: The vehicle's identity, logging setup, and configured sensor
        labels.
    vessel: The support vessel's curated identity and its sensor roster; empty
        until enrichment fills it.
    squidle: Curated Squidle+ identity; empty until ``deployment
        enrich-squidle`` fills it.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_start_datetime: datetime
    deployment_end_datetime: datetime | None = None

    metadata: DeploymentMetadata
    files: FileDescriptorSection
    telemetry: TelemetryDescriptorSection
    platform: PlatformDescriptorSection
    system: SystemDescriptorSection

    vessel: VesselDescriptorSection = Field(
        default_factory=VesselDescriptorSection
    )
    squidle: SquidleDescriptorSection = Field(
        default_factory=SquidleDescriptorSection
    )

    @model_validator(mode="after")
    def _check_temporal_range(self) -> Self:
        validate_temporal_range(
            self.deployment_start_datetime, self.deployment_end_datetime
        )
        return self
