"""Enrichment of deployment descriptors from a curated deployment catalog."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict

from .catalog_types import (
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensorIdentity,
    CatalogVesselProfile,
    DeploymentCatalog,
)
from .descriptor_types import (
    DeploymentDescriptor,
    DeploymentPlatformSection,
    DeploymentVesselSection,
    PlatformIdentity,
    PlatformSensor,
    SensorExtrinsics,
    SensorIdentity,
    VesselIdentity,
    VesselSensor,
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
    """

    model_config = ConfigDict(frozen=True)

    descriptor: DeploymentDescriptor
    platform_matched: bool | None = None
    vessel_matched: bool | None = None


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
    The enriched descriptor and which requested sections resolved.
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

    return DeploymentEnrichment(
        descriptor=descriptor.model_copy(update=updates),
        platform_matched=platform_matched,
        vessel_matched=vessel_matched,
    )


def enrich_platform_section(
    section: DeploymentPlatformSection,
    profile: CatalogPlatformProfile,
    identities: dict[CatalogKey, CatalogSensorIdentity],
) -> DeploymentPlatformSection:
    """
    Fill a platform section's curated slots from a platform profile.

    The roster comes from the deployment's system config, so it is preserved
    key by key: a roster key the profile does not carry keeps its empty slots,
    and a profile entry no roster key names is unused.

    Arguments
    ---------
    section: The platform section to enrich.
    profile: The platform profile assigned to the deployment.
    identities: Catalog sensor identities, keyed by catalog key.

    Returns
    -------
    The enriched platform section.
    """
    entries: dict[str, CatalogProfileSensor] = {
        sensor.key: sensor for sensor in profile.sensors
    }
    return section.model_copy(
        update={
            "identity": PlatformIdentity(
                platform_label=profile.platform_label,
                platform_class=profile.platform_class,
                platform_operator=profile.platform_operator,
            ),
            "sensors": [
                PlatformSensor(
                    key=sensor.key,
                    identity=_sensor_identity(
                        entries.get(sensor.key), identities
                    ),
                    extrinsics=_sensor_extrinsics(entries.get(sensor.key)),
                )
                for sensor in section.sensors
            ],
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
            "sensors": [
                VesselSensor(
                    key=sensor.key,
                    identity=_sensor_identity(sensor, identities),
                    extrinsics=_sensor_extrinsics(sensor),
                )
                for sensor in profile.sensors
            ],
        }
    )


def _sensor_identity(
    entry: CatalogProfileSensor | None,
    identities: dict[CatalogKey, CatalogSensorIdentity],
) -> SensorIdentity | None:
    """Resolve a profile sensor's identity reference against the catalog."""
    if entry is None:
        return None
    identity: CatalogSensorIdentity | None = identities.get(entry.identity)
    if identity is None:
        return None
    return SensorIdentity(
        label=identity.label,
        vendor=identity.vendor,
        product=identity.product,
        type=identity.type,
    )


def _sensor_extrinsics(
    entry: CatalogProfileSensor | None,
) -> SensorExtrinsics | None:
    """Convert a profile sensor's curated pose to descriptor extrinsics."""
    if entry is None or entry.extrinsics is None:
        return None
    return SensorExtrinsics(
        locx=entry.extrinsics.locx,
        locy=entry.extrinsics.locy,
        locz=entry.extrinsics.locz,
        rotx=entry.extrinsics.rotx,
        roty=entry.extrinsics.roty,
        rotz=entry.extrinsics.rotz,
    )
