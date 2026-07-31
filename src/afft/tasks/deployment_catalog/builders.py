"""Builders deriving catalog skeleton records from deployment descriptors."""

import re

from afft.deployment import (
    CatalogDeploymentPlatform,
    CatalogDeploymentVessel,
    CatalogPlatformProfile,
    CatalogProfileSensor,
    CatalogSensor,
    CatalogVesselProfile,
    DeploymentDescriptor,
)

from .types import ScaffoldCatalogDiagnostics

_NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-z0-9]+")


def sensor_identity_key(sensor_key: str) -> str:
    """
    Derive a stub sensor identity key from a roster sensor key.

    The identity of the hardware behind a key is not derivable from a
    deployment, so the stub is keyed on the lowercased roster key (``"RDI"``
    -> ``"rdi"``) for the curator to rename once vendor and product are known.

    Arguments
    ---------
    sensor_key: Roster sensor key, as it appears in the system config.

    Returns
    -------
    The stub identity key.
    """
    return _snake_case(sensor_key)


def map_platform_profile_keys(
    descriptors: list[DeploymentDescriptor],
) -> dict[str, str]:
    """
    Assign a platform profile key to each deployment.

    Deployments are grouped by calendar year and vehicle name — the granularity
    platform profiles are curated at. A year that turns out to span two
    mountings is split by hand afterwards.

    Arguments
    ---------
    descriptors: Deployment descriptors to group.

    Returns
    -------
    Mapping from deployment label to platform profile key.
    """
    return {
        descriptor.deployment_label: (
            f"{descriptor.deployment_datetime.year}_"
            f"{_snake_case(descriptor.system.vehicle_name)}"
        )
        for descriptor in descriptors
    }


def map_vessel_profile_keys(
    descriptors: list[DeploymentDescriptor],
    diagnostics: ScaffoldCatalogDiagnostics,
) -> dict[str, str]:
    """
    Assign a vessel profile key to each deployment that had a support vessel.

    The ``usbl_logs`` role is the only evidence a deployment was tracked from a
    vessel, so deployments without it are left unassigned. Deployments are
    grouped by campaign, and the key's era is the month of the campaign's
    earliest deployment.

    Arguments
    ---------
    descriptors: Deployment descriptors to group.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    Mapping from deployment label to vessel profile key, covering only the
    deployments that carry USBL logs.
    """
    tracked: list[DeploymentDescriptor] = []
    for descriptor in descriptors:
        if descriptor.files.usbl_logs:
            tracked.append(descriptor)
        else:
            diagnostics.warning(
                descriptor.deployment_label,
                "no USBL logs; left without a vessel profile",
            )

    campaign_keys: dict[str, str] = {}
    for descriptor in sorted(
        tracked, key=lambda item: item.deployment_datetime
    ):
        campaign: str = descriptor.metadata.acfr_campaign_label
        if campaign not in campaign_keys:
            campaign_keys[campaign] = (
                f"{descriptor.deployment_datetime:%Y%m}_"
                f"{_snake_case(campaign) or 'unknown_campaign'}"
            )

    return {
        descriptor.deployment_label: campaign_keys[
            descriptor.metadata.acfr_campaign_label
        ]
        for descriptor in tracked
    }


def build_sensor_stubs(
    descriptors: list[DeploymentDescriptor],
) -> list[CatalogSensor]:
    """
    Build one sensor identity stub per observed roster sensor key.

    Arguments
    ---------
    descriptors: Deployment descriptors to collect sensor keys from.

    Returns
    -------
    Sensor stubs with empty curated fields, sorted by key.
    """
    identity_keys: set[str] = {
        sensor_identity_key(sensor.key)
        for descriptor in descriptors
        for sensor in descriptor.platform.sensors
    }
    return [
        CatalogSensor(key=key, label="", vendor="", product="", type="")
        for key in sorted(identity_keys)
    ]


def build_platform_profile_stubs(
    descriptors: list[DeploymentDescriptor],
    profile_keys: dict[str, str],
    diagnostics: ScaffoldCatalogDiagnostics,
) -> list[CatalogPlatformProfile]:
    """
    Build one platform profile stub per assigned profile key.

    A profile's sensor list is the union of the roster keys observed across its
    deployments: enrichment fills only the slots whose key matches, so a union
    serves every roster in the group. Extrinsics are omitted rather than
    zero-filled — an all-zero pose is a real mounting here, not a placeholder.

    Arguments
    ---------
    descriptors: Deployment descriptors to collect rosters from.
    profile_keys: Mapping from deployment label to platform profile key.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    Platform profile stubs with empty curated fields, sorted by key.
    """
    rosters: dict[str, set[str]] = {}
    platform_classes: dict[str, str] = {}
    for descriptor in descriptors:
        profile_key: str = profile_keys[descriptor.deployment_label]
        if not descriptor.platform.sensors:
            diagnostics.warning(
                descriptor.deployment_label, "empty platform sensor roster"
            )
        rosters.setdefault(profile_key, set()).update(
            sensor.key for sensor in descriptor.platform.sensors
        )
        platform_classes[profile_key] = descriptor.system.vehicle_name

    return [
        CatalogPlatformProfile(
            key=profile_key,
            platform_label="",
            platform_class=platform_classes[profile_key],
            platform_operator="",
            sensors=[
                CatalogProfileSensor(
                    key=sensor_key, identity=sensor_identity_key(sensor_key)
                )
                for sensor_key in sorted(rosters[profile_key])
            ],
        )
        for profile_key in sorted(rosters)
    ]


def build_vessel_profile_stubs(
    profile_keys: dict[str, str],
) -> list[CatalogVesselProfile]:
    """
    Build one vessel profile stub per assigned profile key.

    The stubs carry no sensors: the support vessel is topside, so neither its
    name nor its transceiver's key and pose appear anywhere in the vehicle's
    data. The curator adds them.

    Arguments
    ---------
    profile_keys: Mapping from deployment label to vessel profile key.

    Returns
    -------
    Vessel profile stubs with an empty name and no sensors, sorted by key.
    """
    return [
        CatalogVesselProfile(key=profile_key, vessel_name="")
        for profile_key in sorted(set(profile_keys.values()))
    ]


def build_deployment_platforms(
    descriptors: list[DeploymentDescriptor],
    profile_keys: dict[str, str],
) -> list[CatalogDeploymentPlatform]:
    """
    Build the per-deployment platform profile assignments.

    Arguments
    ---------
    descriptors: Deployment descriptors to assign.
    profile_keys: Mapping from deployment label to platform profile key.

    Returns
    -------
    One assignment per deployment, sorted by deployment label to match the
    order the catalog is written in.
    """
    return [
        CatalogDeploymentPlatform(
            deployment_label=descriptor.deployment_label,
            platform_profile=profile_keys[descriptor.deployment_label],
        )
        for descriptor in sorted(
            descriptors, key=lambda item: item.deployment_label
        )
    ]


def build_deployment_vessels(
    descriptors: list[DeploymentDescriptor],
    profile_keys: dict[str, str],
) -> list[CatalogDeploymentVessel]:
    """
    Build the per-deployment vessel profile assignments.

    Arguments
    ---------
    descriptors: Deployment descriptors to assign.
    profile_keys: Mapping from deployment label to vessel profile key.

    Returns
    -------
    One assignment per deployment that carries USBL logs, sorted by deployment
    label to match the order the catalog is written in.
    """
    return [
        CatalogDeploymentVessel(
            deployment_label=descriptor.deployment_label,
            vessel_profile=profile_keys[descriptor.deployment_label],
        )
        for descriptor in sorted(
            descriptors, key=lambda item: item.deployment_label
        )
        if descriptor.deployment_label in profile_keys
    ]


def _snake_case(value: str) -> str:
    """Lowercase a label and collapse its non-alphanumeric runs to underscores."""
    return _NON_ALPHANUMERIC_PATTERN.sub("_", value.lower()).strip("_")
