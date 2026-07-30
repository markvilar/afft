"""Curated records that deployment descriptor enrichment resolves against."""

from collections.abc import Iterable
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatalogSensor(BaseModel):
    """
    A curated sensor identity record.

    Attributes
    ----------
    key: Catalog lookup key, referenced by ``CatalogProfileSensor.identity``.
    label: Human-readable sensor name.
    vendor: Manufacturer.
    product: Product name.
    type: Sensor type.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    vendor: str
    product: str
    type: str


class CatalogSensorExtrinsics(BaseModel):
    """
    A curated mounting pose, in the reference frame of the containing profile.

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


class CatalogProfileSensor(BaseModel):
    """
    A sensor mounted on a platform or vessel profile.

    Attributes
    ----------
    key: Sensor identifier, matched against ``PlatformSensor.key`` /
        ``VesselSensor.key`` during enrichment.
    identity: Key of the ``CatalogSensor`` describing this hardware.
    extrinsics: Curated mounting pose; ``None`` where the sensor has no
        surveyed pose.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    identity: str
    extrinsics: CatalogSensorExtrinsics | None = None


class CatalogPlatformProfile(BaseModel):
    """
    A platform configuration at a point in time.

    Attributes
    ----------
    key: Profile lookup key.
    platform_label: Human-readable platform name.
    platform_class: Vehicle class, matching ``system.vehicle_name``.
    platform_operator: Operating institution.
    sensors: The platform's sensor roster, with poses in the vehicle (SNAME)
        body frame.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    platform_label: str
    platform_class: str
    platform_operator: str
    sensors: list[CatalogProfileSensor] = Field(default_factory=list)


class CatalogVesselProfile(BaseModel):
    """
    A support vessel configuration at a point in time.

    Attributes
    ----------
    key: Profile lookup key.
    vessel_name: Support vessel name.
    sensors: The vessel's sensor roster, with poses in the ship reference
        frame.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    vessel_name: str
    sensors: list[CatalogProfileSensor] = Field(default_factory=list)


class CatalogDeploymentPlatform(BaseModel):
    """
    Assignment of a platform profile to a deployment.

    Attributes
    ----------
    deployment_label: Label of the assigned deployment.
    platform_profile: Key of the assigned ``CatalogPlatformProfile``.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    platform_profile: str


class CatalogDeploymentVessel(BaseModel):
    """
    Assignment of a vessel profile to a deployment.

    Attributes
    ----------
    deployment_label: Label of the assigned deployment.
    vessel_profile: Key of the assigned ``CatalogVesselProfile``.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    vessel_profile: str


class DeploymentCatalog(BaseModel):
    """
    Curated records that enrichment resolves deployment descriptors against.

    A catalog of the platforms, vessels, and sensors deployments are enriched
    from — not a catalog of the deployments themselves.

    Attributes
    ----------
    sensors: Sensor identity records.
    platform_profiles: Platform configurations.
    vessel_profiles: Vessel configurations.
    deployment_platforms: Per-deployment platform profile assignments.
    deployment_vessels: Per-deployment vessel profile assignments.
    """

    model_config = ConfigDict(frozen=True)

    sensors: list[CatalogSensor] = Field(default_factory=list)
    platform_profiles: list[CatalogPlatformProfile] = Field(
        default_factory=list
    )
    vessel_profiles: list[CatalogVesselProfile] = Field(default_factory=list)
    deployment_platforms: list[CatalogDeploymentPlatform] = Field(
        default_factory=list
    )
    deployment_vessels: list[CatalogDeploymentVessel] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        """
        Check the whole-file rules a single record cannot enforce.

        Keys must be unique within each record table, each deployment may be
        assigned at most one profile of each kind, and every cross-reference
        must resolve. A dangling reference is a curation error rather than a
        missing record, so it fails at load.

        Returns
        -------
        The validated catalog.

        Raises
        ------
        ValueError: If a key is duplicated, a deployment is assigned twice, or
            a reference names no record.
        """
        sensor_keys: set[str] = _unique_keys(
            (sensor.key for sensor in self.sensors), "sensors"
        )
        platform_profile_keys: set[str] = _unique_keys(
            (profile.key for profile in self.platform_profiles),
            "platform_profiles",
        )
        vessel_profile_keys: set[str] = _unique_keys(
            (profile.key for profile in self.vessel_profiles),
            "vessel_profiles",
        )

        _unique_keys(
            (entry.deployment_label for entry in self.deployment_platforms),
            "deployment_platforms",
        )
        _unique_keys(
            (entry.deployment_label for entry in self.deployment_vessels),
            "deployment_vessels",
        )

        for platform_profile in self.platform_profiles:
            _check_sensor_identities(
                platform_profile.key, platform_profile.sensors, sensor_keys
            )
        for vessel_profile in self.vessel_profiles:
            _check_sensor_identities(
                vessel_profile.key, vessel_profile.sensors, sensor_keys
            )

        for platform_entry in self.deployment_platforms:
            if platform_entry.platform_profile not in platform_profile_keys:
                raise ValueError(
                    f"deployment {platform_entry.deployment_label!r} references "
                    f"unknown platform profile: "
                    f"{platform_entry.platform_profile!r}"
                )
        for vessel_entry in self.deployment_vessels:
            if vessel_entry.vessel_profile not in vessel_profile_keys:
                raise ValueError(
                    f"deployment {vessel_entry.deployment_label!r} references "
                    f"unknown vessel profile: {vessel_entry.vessel_profile!r}"
                )

        return self


def _unique_keys(keys: Iterable[str], table: str) -> set[str]:
    """Collect keys into a set, raising on the first duplicate."""
    unique: set[str] = set()
    for key in keys:
        if key in unique:
            raise ValueError(f"duplicate key in {table}: {key!r}")
        unique.add(key)
    return unique


def _check_sensor_identities(
    profile_key: str,
    sensors: list[CatalogProfileSensor],
    sensor_keys: set[str],
) -> None:
    """Check that every profile sensor identity names a catalog sensor."""
    for sensor in sensors:
        if sensor.identity not in sensor_keys:
            raise ValueError(
                f"profile {profile_key!r} sensor {sensor.key!r} references "
                f"unknown sensor identity: {sensor.identity!r}"
            )
