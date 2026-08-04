"""Aggregate views over a curated deployment catalog."""

from pydantic import BaseModel, ConfigDict, Field

from .catalog_types import (
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensorIdentity,
    CatalogVesselProfile,
    DeploymentCatalog,
)

type FieldName = str
type ProfileKey = str
type RecordKey = str
type CatalogRecord = (
    CatalogSensorIdentity | CatalogPlatformProfile | CatalogVesselProfile
)


class ProfileAssignment(BaseModel):
    """
    A profile and the deployments assigned to it.

    Attributes
    ----------
    profile_key: Key of the assigned profile.
    deployment_labels: Labels of the deployments assigned the profile, in
        alphabetical order.
    """

    model_config = ConfigDict(frozen=True)

    profile_key: ProfileKey
    deployment_labels: list[str]

    @property
    def count(self) -> int:
        """Number of deployments assigned the profile."""
        return len(self.deployment_labels)


class AssignmentCoverage(BaseModel):
    """
    Profile assignment coverage across the deployments the catalog names.

    A catalog knows a deployment only through its assignment tables, so the
    deployments covered are those named by either table.

    Attributes
    ----------
    deployment_labels: Labels named by either assignment table, in alphabetical
        order.
    platform_only: Labels assigned a platform profile but no vessel profile.
    vessel_only: Labels assigned a vessel profile but no platform profile.
    """

    model_config = ConfigDict(frozen=True)

    deployment_labels: list[str]
    platform_only: list[str]
    vessel_only: list[str]

    @property
    def deployment_count(self) -> int:
        """Number of deployments the catalog names."""
        return len(self.deployment_labels)

    @property
    def with_platform(self) -> int:
        """Number of deployments assigned a platform profile."""
        return self.deployment_count - len(self.vessel_only)

    @property
    def with_vessel(self) -> int:
        """Number of deployments assigned a vessel profile."""
        return self.deployment_count - len(self.platform_only)


class CatalogCurationGap(BaseModel):
    """
    A curated slot left unfilled across one or more catalog records.

    Attributes
    ----------
    field_name: Dotted path of the unfilled field, e.g.
        ``"platform_profiles.platform_label"``.
    record_keys: Keys of the records the slot is unfilled for.
    """

    model_config = ConfigDict(frozen=True)

    field_name: FieldName
    record_keys: list[RecordKey]

    @property
    def count(self) -> int:
        """Number of records the slot is unfilled for."""
        return len(self.record_keys)


class CatalogSummary(BaseModel):
    """
    Aggregate summary of a curated deployment catalog file.

    Attributes
    ----------
    sensor_identity_count: Number of sensor identity records.
    platform_profile_count: Number of platform profile records.
    vessel_profile_count: Number of vessel profile records.
    coverage: Profile assignment coverage across the named deployments.
    platform_assignments: Every platform profile and its assigned deployments.
    vessel_assignments: Every vessel profile and its assigned deployments.
    unreferenced_sensors: Keys of the sensor identities no profile sensor
        references.
    curation_gaps: Unfilled curated slots, per field.
    """

    model_config = ConfigDict(frozen=True)

    sensor_identity_count: int
    platform_profile_count: int
    vessel_profile_count: int
    coverage: AssignmentCoverage
    platform_assignments: list[ProfileAssignment] = Field(default_factory=list)
    vessel_assignments: list[ProfileAssignment] = Field(default_factory=list)
    unreferenced_sensors: list[RecordKey] = Field(default_factory=list)
    curation_gaps: list[CatalogCurationGap] = Field(default_factory=list)


def _collect_coverage(catalog: DeploymentCatalog) -> AssignmentCoverage:
    """Collect the assignment coverage of the deployments the catalog names."""
    platform_labels: set[str] = {
        entry.deployment_label for entry in catalog.deployment_platforms
    }
    vessel_labels: set[str] = {
        entry.deployment_label for entry in catalog.deployment_vessels
    }
    return AssignmentCoverage(
        deployment_labels=sorted(platform_labels | vessel_labels),
        platform_only=sorted(platform_labels - vessel_labels),
        vessel_only=sorted(vessel_labels - platform_labels),
    )


def _collect_assignments(
    profile_keys: list[ProfileKey],
    labels_by_profile: dict[ProfileKey, list[str]],
) -> list[ProfileAssignment]:
    """
    Pair every profile with its assigned deployments, ordered by descending
    assignment count, then by profile key.
    """
    assignments: list[ProfileAssignment] = [
        ProfileAssignment(
            profile_key=profile_key,
            deployment_labels=sorted(labels_by_profile.get(profile_key, [])),
        )
        for profile_key in profile_keys
    ]
    return sorted(
        assignments, key=lambda entry: (-entry.count, entry.profile_key)
    )


def _collect_platform_assignments(
    catalog: DeploymentCatalog,
) -> list[ProfileAssignment]:
    """Pair every platform profile with its assigned deployments."""
    labels_by_profile: dict[ProfileKey, list[str]] = {}
    for entry in catalog.deployment_platforms:
        labels_by_profile.setdefault(entry.platform_profile, []).append(
            entry.deployment_label
        )
    return _collect_assignments(
        [profile.key for profile in catalog.platform_profiles],
        labels_by_profile,
    )


def _collect_vessel_assignments(
    catalog: DeploymentCatalog,
) -> list[ProfileAssignment]:
    """Pair every vessel profile with its assigned deployments."""
    labels_by_profile: dict[ProfileKey, list[str]] = {}
    for entry in catalog.deployment_vessels:
        labels_by_profile.setdefault(entry.vessel_profile, []).append(
            entry.deployment_label
        )
    return _collect_assignments(
        [profile.key for profile in catalog.vessel_profiles], labels_by_profile
    )


def collect_unreferenced_sensors(
    catalog: DeploymentCatalog,
) -> list[RecordKey]:
    """
    Collect the sensor identities no profile mounts.

    Not every unmounted identity is an oversight: the catalog keeps reference
    records for hardware the vehicle carried but nothing downstream consumes,
    such as the thrusters and the obstacle avoidance sonar. They are reported
    all the same, since the record itself does not say which it is.

    Arguments
    ---------
    catalog: Deployment catalog to inspect.

    Returns
    -------
    Keys of the unmounted sensor identities, in file order.
    """
    profiles: list[CatalogPlatformProfile | CatalogVesselProfile] = [
        *catalog.platform_profiles,
        *catalog.vessel_profiles,
    ]
    referenced: set[str] = {
        sensor.key for profile in profiles for sensor in profile.sensors
    }
    return [
        sensor.key
        for sensor in catalog.sensor_identities
        if sensor.key not in referenced
    ]


def _sensor_pose_gaps(
    profile_key: ProfileKey,
    sensors: list[CatalogProfileSensor],
) -> list[RecordKey]:
    """Collect the profile sensors left without a mounting pose."""
    return [
        f"{profile_key}[{sensor.key}]"
        for sensor in sensors
        if sensor.extrinsics is None
    ]


def _empty_fields(
    record: CatalogRecord,
    fields: tuple[str, ...],
    section: str,
) -> list[tuple[FieldName, RecordKey]]:
    """Pair every empty string field of a record with the record's key."""
    return [
        (f"{section}.{field}", record.key)
        for field in fields
        if not getattr(record, field)
    ]


def collect_catalog_curation_gaps(
    catalog: DeploymentCatalog,
) -> list[CatalogCurationGap]:
    """
    Collect the catalog's unfilled curated slots, grouped per field.

    A slot is unfilled when a curated string field is empty, or when a profile
    sensor carries no mounting pose.

    Arguments
    ---------
    catalog: Deployment catalog to inspect.

    Returns
    -------
    Gaps ordered by descending record count, then by field name.
    """
    keys_by_field: dict[FieldName, list[RecordKey]] = {}

    def add(field_name: FieldName, record_key: RecordKey) -> None:
        keys_by_field.setdefault(field_name, []).append(record_key)

    for sensor_identity in catalog.sensor_identities:
        for field_name, record_key in _empty_fields(
            sensor_identity,
            ("label", "vendor", "product", "type"),
            "sensor_identities",
        ):
            add(field_name, record_key)

    for platform_profile in catalog.platform_profiles:
        for field_name, record_key in _empty_fields(
            platform_profile,
            ("platform_label", "platform_class", "platform_operator"),
            "platform_profiles",
        ):
            add(field_name, record_key)
        for sensor_key in _sensor_pose_gaps(
            platform_profile.key, platform_profile.sensors
        ):
            add("platform_profiles.sensors.extrinsics", sensor_key)

    for vessel_profile in catalog.vessel_profiles:
        for field_name, record_key in _empty_fields(
            vessel_profile, ("vessel_name",), "vessel_profiles"
        ):
            add(field_name, record_key)
        for sensor_key in _sensor_pose_gaps(
            vessel_profile.key, vessel_profile.sensors
        ):
            add("vessel_profiles.sensors.extrinsics", sensor_key)

    return [
        CatalogCurationGap(field_name=field_name, record_keys=record_keys)
        for field_name, record_keys in sorted(
            keys_by_field.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]


def summarize_catalog(catalog: DeploymentCatalog) -> CatalogSummary:
    """
    Aggregate a curated deployment catalog into a summary.

    Referential integrity is left to ``DeploymentCatalog.validate_catalog``;
    what is reported here is curation progress — empty curated fields, and
    records nothing references or assigns.

    Arguments
    ---------
    catalog: Deployment catalog to summarize.

    Returns
    -------
    The computed summary. An empty catalog summarizes to zero counts.
    """
    return CatalogSummary(
        sensor_identity_count=len(catalog.sensor_identities),
        platform_profile_count=len(catalog.platform_profiles),
        vessel_profile_count=len(catalog.vessel_profiles),
        coverage=_collect_coverage(catalog),
        platform_assignments=_collect_platform_assignments(catalog),
        vessel_assignments=_collect_vessel_assignments(catalog),
        unreferenced_sensors=collect_unreferenced_sensors(catalog),
        curation_gaps=collect_catalog_curation_gaps(catalog),
    )
