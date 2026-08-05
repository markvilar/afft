"""Aggregate views over a set of deployment descriptors."""

from collections import Counter
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common_types import PlatformSensor, SensorIdentity, VesselSensor
from .descriptor_types import DeploymentDescriptor, DeploymentFileSection

type FieldName = str
type CampaignLabel = str
type TopicName = str
type SectionName = str


class GeographicExtent(BaseModel):
    """
    Bounding box of the deployment origins.

    Attributes
    ----------
    min_latitude: Southernmost origin latitude in degrees.
    max_latitude: Northernmost origin latitude in degrees.
    min_longitude: Westernmost origin longitude in degrees.
    max_longitude: Easternmost origin longitude in degrees.
    """

    model_config = ConfigDict(frozen=True)

    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float


class CurationGap(BaseModel):
    """
    A curated slot left unfilled across one or more deployments.

    Attributes
    ----------
    field_name: Dotted path of the unfilled field, e.g.
        ``"platform.identity.platform_label"``.
    deployment_labels: Labels of the deployments the slot is unfilled for.
    """

    model_config = ConfigDict(frozen=True)

    field_name: FieldName
    deployment_labels: list[str]

    @property
    def count(self) -> int:
        """Number of deployments the slot is unfilled for."""
        return len(self.deployment_labels)


class DeploymentSummary(BaseModel):
    """
    Per-deployment detail, written only to the report file.

    Attributes
    ----------
    deployment_label: Label of the summarized deployment.
    deployment_datetime: Deployment datetime.
    campaign_label: ACFR campaign the deployment belongs to.
    file_counts: File count per file section name.
    topics: Telemetry topics observed for the deployment.
    platform_sensor_keys: Keys of the platform's sensors.
    vessel_sensor_keys: Keys of the vessel's sensors.
    unfilled_fields: Dotted paths of the deployment's unfilled curated slots.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_datetime: datetime
    campaign_label: str
    file_counts: dict[SectionName, int]
    topics: list[TopicName]
    platform_sensor_keys: list[str]
    vessel_sensor_keys: list[str]
    unfilled_fields: list[FieldName]


class DescriptorSummary(BaseModel):
    """
    Aggregate summary of a deployment descriptor file.

    Attributes
    ----------
    deployment_count: Number of deployments in the file.
    campaign_counts: Deployment count per campaign label.
    earliest_datetime: Earliest deployment datetime.
    latest_datetime: Latest deployment datetime.
    extent: Bounding box of the deployment origins.
    section_coverage: Number of deployments with a non-empty file section,
        per section name.
    topic_counts: Number of deployments reporting a topic, per topic name.
    enriched: Whether any deployment carries a platform identity.
    curation_gaps: Unfilled curated slots, per field; empty when the
        descriptors are not enriched.
    deployments: Per-deployment detail, in file order.
    """

    model_config = ConfigDict(frozen=True)

    deployment_count: int
    campaign_counts: dict[CampaignLabel, int]
    earliest_datetime: datetime
    latest_datetime: datetime
    extent: GeographicExtent
    section_coverage: dict[SectionName, int]
    topic_counts: dict[TopicName, int]
    enriched: bool
    curation_gaps: list[CurationGap] = Field(default_factory=list)
    deployments: list[DeploymentSummary] = Field(default_factory=list)


def _sort_counts(counts: Counter[str]) -> dict[str, int]:
    """Order counts by descending count, then by name."""
    return {
        name: count
        for name, count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )
    }


def _empty_identity_fields(
    identity: SensorIdentity,
    prefix: str,
) -> list[FieldName]:
    """Collect the empty string fields of a sensor identity."""
    return [
        f"{prefix}.{field}"
        for field in ("label", "vendor", "product", "type")
        if not getattr(identity, field)
    ]


def _sensor_gaps(
    sensors: list[PlatformSensor] | list[VesselSensor],
    section: str,
) -> list[FieldName]:
    """
    Collect the unfilled slots of a platform or vessel sensor roster.

    A roster is written whole by enrichment, so a sensor that exists at all
    has an identity: the gaps are the identity's empty fields and a missing
    pose. An unenriched descriptor shows up as an empty roster instead.
    """
    unfilled: list[FieldName] = []
    for sensor in sensors:
        prefix: str = f"{section}.sensors[{sensor.key}]"
        if sensor.identity is not None:
            unfilled.extend(
                _empty_identity_fields(sensor.identity, f"{prefix}.identity")
            )
        if sensor.extrinsics is None:
            unfilled.append(f"{prefix}.extrinsics")
    return unfilled


def collect_unfilled_fields(
    descriptor: DeploymentDescriptor,
) -> list[FieldName]:
    """
    Collect the dotted paths of a deployment's unfilled curated slots.

    A slot is unfilled when its model field is ``None``, or when a string
    field is empty.

    Arguments
    ---------
    descriptor: Deployment descriptor to inspect.

    Returns
    -------
    Dotted paths of the unfilled slots, in declaration order.
    """
    unfilled: list[FieldName] = []

    if not descriptor.metadata.acfr_platform_label:
        unfilled.append("metadata.acfr_platform_label")

    platform_identity = descriptor.platform.identity
    if platform_identity is None:
        unfilled.append("platform.identity")
    else:
        unfilled.extend(
            f"platform.identity.{field}"
            for field in (
                "platform_label",
                "platform_class",
                "platform_operator",
            )
            if not getattr(platform_identity, field)
        )

    unfilled.extend(_sensor_gaps(descriptor.platform.sensors, "platform"))

    vessel_identity = descriptor.vessel.identity
    if vessel_identity is None:
        unfilled.append("vessel.identity")
    elif not vessel_identity.vessel_name:
        unfilled.append("vessel.identity.vessel_name")

    unfilled.extend(_sensor_gaps(descriptor.vessel.sensors, "vessel"))

    return unfilled


def _summarize_deployment(
    descriptor: DeploymentDescriptor,
) -> DeploymentSummary:
    """Build the per-deployment detail for one descriptor."""
    return DeploymentSummary(
        deployment_label=descriptor.deployment_label,
        deployment_datetime=descriptor.deployment_datetime,
        campaign_label=descriptor.metadata.acfr_campaign_label,
        file_counts={
            section: len(getattr(descriptor.files, section))
            for section in DeploymentFileSection.model_fields
        },
        topics=list(descriptor.telemetry.topics),
        platform_sensor_keys=[
            sensor.key for sensor in descriptor.platform.sensors
        ],
        vessel_sensor_keys=[sensor.key for sensor in descriptor.vessel.sensors],
        unfilled_fields=collect_unfilled_fields(descriptor),
    )


def summarize_descriptors(
    descriptors: list[DeploymentDescriptor],
) -> DescriptorSummary:
    """
    Aggregate a set of deployment descriptors into a summary.

    An un-enriched set has every curated slot unfilled, which degenerates into
    one gap per field listing every deployment. That case is reported as
    unenriched instead, and carries no curation gaps.

    Arguments
    ---------
    descriptors: Deployment descriptors to summarize.

    Returns
    -------
    The computed summary, including per-deployment detail.

    Raises
    ------
    ValueError: If no descriptors were given.
    """
    if not descriptors:
        raise ValueError("cannot summarize an empty set of descriptors")

    deployments: list[DeploymentSummary] = [
        _summarize_deployment(descriptor) for descriptor in descriptors
    ]

    campaign_counts: Counter[CampaignLabel] = Counter(
        deployment.campaign_label for deployment in deployments
    )
    topic_counts: Counter[TopicName] = Counter(
        topic for deployment in deployments for topic in deployment.topics
    )
    section_coverage: dict[SectionName, int] = {
        section: sum(
            1
            for deployment in deployments
            if deployment.file_counts[section] > 0
        )
        for section in DeploymentFileSection.model_fields
    }

    latitudes: list[float] = [
        descriptor.metadata.origin_latitude for descriptor in descriptors
    ]
    longitudes: list[float] = [
        descriptor.metadata.origin_longitude for descriptor in descriptors
    ]

    enriched: bool = any(
        descriptor.platform.identity is not None for descriptor in descriptors
    )

    return DescriptorSummary(
        deployment_count=len(descriptors),
        campaign_counts=_sort_counts(campaign_counts),
        earliest_datetime=min(
            deployment.deployment_datetime for deployment in deployments
        ),
        latest_datetime=max(
            deployment.deployment_datetime for deployment in deployments
        ),
        extent=GeographicExtent(
            min_latitude=min(latitudes),
            max_latitude=max(latitudes),
            min_longitude=min(longitudes),
            max_longitude=max(longitudes),
        ),
        section_coverage=section_coverage,
        topic_counts=_sort_counts(topic_counts),
        enriched=enriched,
        curation_gaps=collect_curation_gaps(deployments) if enriched else [],
        deployments=deployments,
    )


def collect_curation_gaps(
    deployments: list[DeploymentSummary],
) -> list[CurationGap]:
    """
    Group the per-deployment unfilled slots into one gap per field.

    Arguments
    ---------
    deployments: Per-deployment summaries to group.

    Returns
    -------
    Gaps ordered by descending deployment count, then by field name.
    """
    labels_by_field: dict[FieldName, list[str]] = {}
    for deployment in deployments:
        for field_name in deployment.unfilled_fields:
            labels_by_field.setdefault(field_name, []).append(
                deployment.deployment_label
            )

    return [
        CurationGap(field_name=field_name, deployment_labels=labels)
        for field_name, labels in sorted(
            labels_by_field.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]
