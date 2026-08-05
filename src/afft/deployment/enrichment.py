"""Enrichment of deployment descriptors from a curated deployment catalog."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from .catalog_types import (
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensorIdentity,
    CatalogVesselProfile,
    DeploymentCatalog,
)
from .common_types import (
    PlatformIdentity,
    PlatformSensor,
    SensorExtrinsics,
    SensorIdentity,
    VesselIdentity,
    VesselSensor,
)
from .descriptor_types import (
    DeploymentDescriptor,
    DeploymentPlatformSection,
    DeploymentVesselSection,
)

type CatalogKey = str
type DeploymentLabel = str


class EnrichmentSection(StrEnum):
    """The descriptor sections enrichment can be asked to fill."""

    PLATFORM = "platform"
    VESSEL = "vessel"
    ALL = "all"


class DeploymentCatalogIndex(BaseModel):
    """
    The catalog's record tables keyed for lookup, built once per run.

    Attributes
    ----------
    sensor_identities: Sensor identity records, keyed by catalog key.
    platform_profiles: Platform profiles, keyed by catalog key.
    vessel_profiles: Vessel profiles, keyed by catalog key.
    platform_assignments: Platform profile key, per deployment label.
    vessel_assignments: Vessel profile key, per deployment label.
    """

    model_config = ConfigDict(frozen=True)

    sensor_identities: dict[CatalogKey, CatalogSensorIdentity]
    platform_profiles: dict[CatalogKey, CatalogPlatformProfile]
    vessel_profiles: dict[CatalogKey, CatalogVesselProfile]
    platform_assignments: dict[DeploymentLabel, CatalogKey]
    vessel_assignments: dict[DeploymentLabel, CatalogKey]

    @classmethod
    def from_catalog(cls, catalog: DeploymentCatalog) -> Self:
        """
        Index a catalog for lookup by deployment label and record key.

        Arguments
        ---------
        catalog: The curated catalog to index.

        Returns
        -------
        The indexed catalog.
        """
        return cls(
            sensor_identities={
                sensor.key: sensor for sensor in catalog.sensor_identities
            },
            platform_profiles={
                profile.key: profile for profile in catalog.platform_profiles
            },
            vessel_profiles={
                profile.key: profile for profile in catalog.vessel_profiles
            },
            platform_assignments={
                entry.deployment_label: entry.platform_profile
                for entry in catalog.deployment_platforms
            },
            vessel_assignments={
                entry.deployment_label: entry.vessel_profile
                for entry in catalog.deployment_vessels
            },
        )

    def platform_profile(
        self, deployment_label: DeploymentLabel
    ) -> CatalogPlatformProfile | None:
        """
        Look up the platform profile assigned to a deployment.

        Arguments
        ---------
        deployment_label: Label of the deployment to look up.

        Returns
        -------
        The assigned platform profile, or ``None`` if the deployment has no
        assignment.
        """
        key: CatalogKey | None = self.platform_assignments.get(deployment_label)
        return self.platform_profiles.get(key) if key is not None else None

    def vessel_profile(
        self, deployment_label: DeploymentLabel
    ) -> CatalogVesselProfile | None:
        """
        Look up the vessel profile assigned to a deployment.

        Arguments
        ---------
        deployment_label: Label of the deployment to look up.

        Returns
        -------
        The assigned vessel profile, or ``None`` if the deployment has no
        assignment.
        """
        key: CatalogKey | None = self.vessel_assignments.get(deployment_label)
        return self.vessel_profiles.get(key) if key is not None else None


class DeploymentEnrichment(BaseModel):
    """
    A descriptor with its curated slots filled, and whether each requested
    section resolved to a catalog profile. A ``None`` flag means the section
    was not requested.

    Attributes
    ----------
    descriptor: The enriched descriptor.
    platform_matched: Whether the platform section resolved to a profile;
        ``None`` if the platform section was not requested.
    vessel_matched: Whether the vessel section resolved to a profile; ``None``
        if the vessel section was not requested.
    undeclared_topics: Topics the deployment logged that no curated sensor
        claims, sorted.
    unobserved_topics: Topics the curated roster declares that the deployment
        never logged, sorted.
    """

    model_config = ConfigDict(frozen=True)

    descriptor: DeploymentDescriptor
    platform_matched: bool | None = None
    vessel_matched: bool | None = None
    undeclared_topics: list[str] = Field(default_factory=list)
    unobserved_topics: list[str] = Field(default_factory=list)


def enrich_descriptor(
    descriptor: DeploymentDescriptor,
    index: DeploymentCatalogIndex,
    section: EnrichmentSection = EnrichmentSection.ALL,
) -> DeploymentEnrichment:
    """
    Fill a descriptor's curated slots from an indexed catalog.

    The catalog is authoritative: the requested sections are filled from it
    whatever they held before, so enrichment is a pure function of the
    descriptor and the catalog. Sections that were not requested are left
    exactly as the descriptor held them.

    Arguments
    ---------
    descriptor: The descriptor to enrich.
    index: The indexed catalog to resolve curated records against.
    section: The sections to fill.

    Returns
    -------
    The enriched descriptor, which requested sections resolved, and how the
    resolved roster's declared topics compare to the observed ones.
    """
    updates: dict[str, DeploymentPlatformSection | DeploymentVesselSection] = {}
    platform_matched: bool | None = None
    vessel_matched: bool | None = None

    if section in (EnrichmentSection.PLATFORM, EnrichmentSection.ALL):
        platform_profile: CatalogPlatformProfile | None = (
            index.platform_profile(descriptor.deployment_label)
        )
        platform_matched = platform_profile is not None
        if platform_profile is not None:
            updates["platform"] = enrich_platform_section(
                descriptor.platform, platform_profile, index.sensor_identities
            )

    if section in (EnrichmentSection.VESSEL, EnrichmentSection.ALL):
        vessel_profile: CatalogVesselProfile | None = index.vessel_profile(
            descriptor.deployment_label
        )
        vessel_matched = vessel_profile is not None
        if vessel_profile is not None:
            updates["vessel"] = enrich_vessel_section(
                descriptor.vessel, vessel_profile, index.sensor_identities
            )

    enriched: DeploymentDescriptor = descriptor.model_copy(update=updates)
    undeclared_topics: list[str] = []
    unobserved_topics: list[str] = []
    # The platform sensors own the RAW topics, so the comparison only means
    # something once their roster is the curated one.
    if platform_matched:
        undeclared_topics, unobserved_topics = compare_topics(enriched)

    return DeploymentEnrichment(
        descriptor=enriched,
        platform_matched=platform_matched,
        vessel_matched=vessel_matched,
        undeclared_topics=undeclared_topics,
        unobserved_topics=unobserved_topics,
    )


def compare_topics(
    descriptor: DeploymentDescriptor,
) -> tuple[list[str], list[str]]:
    """
    Compare the topics a descriptor's curated roster declares against the
    topics its deployment logged.

    A mismatch is a curation signal rather than an error in either direction:
    a sensor can be fitted and log nothing, and a logged topic can belong to
    hardware the catalog deliberately leaves unmounted.

    Arguments
    ---------
    descriptor: Enriched descriptor to check.

    Returns
    -------
    The observed topics no sensor claims and the declared topics the
    deployment never logged, each sorted.
    """
    sensors: list[PlatformSensor | VesselSensor] = [
        *descriptor.platform.sensors,
        *descriptor.vessel.sensors,
    ]
    declared: set[str] = {
        topic for sensor in sensors for topic in sensor.message_topics
    }
    observed: set[str] = set(descriptor.telemetry.topics)
    return sorted(observed - declared), sorted(declared - observed)


def enrich_platform_section(
    section: DeploymentPlatformSection,
    profile: CatalogPlatformProfile,
    identities: dict[CatalogKey, CatalogSensorIdentity],
) -> DeploymentPlatformSection:
    """
    Fill a platform section from a platform profile.

    Every field of the section is curated — the deployment data names the
    vehicle's sensors only by system config label, a vocabulary of its own —
    so the profile's roster replaces the section's contents outright.

    Arguments
    ---------
    section: The platform section to enrich.
    profile: The platform profile assigned to the deployment.
    identities: Catalog sensor identities, keyed by catalog key.

    Returns
    -------
    The enriched platform section.
    """
    return section.model_copy(
        update={
            "identity": PlatformIdentity(
                platform_label=profile.platform_label,
                platform_class=profile.platform_class,
                platform_operator=profile.platform_operator,
            ),
            "sensors": _resolve_sensors(
                profile.sensors, identities, PlatformSensor
            ),
        }
    )


def enrich_vessel_section(
    section: DeploymentVesselSection,
    profile: CatalogVesselProfile,
    identities: dict[CatalogKey, CatalogSensorIdentity],
) -> DeploymentVesselSection:
    """
    Fill a vessel section from a vessel profile.

    Every field of the section is curated — nothing in the deployment data
    names the support vessel — so the profile's roster replaces the section's
    contents outright rather than filling slots around derived content.

    Arguments
    ---------
    section: The vessel section to enrich.
    profile: The vessel profile assigned to the deployment.
    identities: Catalog sensor identities, keyed by catalog key.

    Returns
    -------
    The enriched vessel section.
    """
    return section.model_copy(
        update={
            "identity": VesselIdentity(vessel_name=profile.vessel_name),
            "sensors": _resolve_sensors(
                profile.sensors, identities, VesselSensor
            ),
        }
    )


def _resolve_sensors[SensorT: (PlatformSensor, VesselSensor)](
    sensors: list[CatalogProfileSensor],
    identities: dict[CatalogKey, CatalogSensorIdentity],
    sensor_type: type[SensorT],
) -> list[SensorT]:
    """
    Resolve a profile's roster into descriptor sensors.

    The two bodies differ only in which sensor model their roster holds: both
    key a sensor on its catalog identity, and both carry the curated topic
    mapping and pose through unchanged.
    """
    return [
        sensor_type(
            key=sensor.key,
            message_topics=list(sensor.message_topics),
            identity=_sensor_identity(sensor, identities),
            extrinsics=_sensor_extrinsics(sensor),
        )
        for sensor in sensors
    ]


def _sensor_identity(
    entry: CatalogProfileSensor,
    identities: dict[CatalogKey, CatalogSensorIdentity],
) -> SensorIdentity | None:
    """Resolve a profile sensor's key against the catalog identity records."""
    identity: CatalogSensorIdentity | None = identities.get(entry.key)
    if identity is None:
        return None
    return SensorIdentity(
        label=identity.label,
        vendor=identity.vendor,
        product=identity.product,
        type=identity.type,
    )


def _sensor_extrinsics(
    entry: CatalogProfileSensor,
) -> SensorExtrinsics | None:
    """Convert a profile sensor's curated pose to descriptor extrinsics."""
    if entry.extrinsics is None:
        return None
    return SensorExtrinsics(
        locx=entry.extrinsics.locx,
        locy=entry.extrinsics.locy,
        locz=entry.extrinsics.locz,
        rotx=entry.extrinsics.rotx,
        roty=entry.extrinsics.roty,
        rotz=entry.extrinsics.rotz,
    )
