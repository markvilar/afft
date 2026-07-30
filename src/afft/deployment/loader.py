"""Loaders for deployment configuration and metadata from TOML files."""

import json
import math

import msgspec

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .catalog import CatalogProfileSensor, DeploymentCatalog
from .descriptor import DeploymentDescriptor
from .types import (
    DeploymentConfig,
    DeploymentInfo,
    TopsideUsblModemConfig,
    UsblUncertaintyProfile,
)


def load_deployment_config(
    path: Path,
    deployment_label: str,
) -> DeploymentConfig:
    """Load a deployment configuration by label from a TOML file.

    Arguments
    ---------
    path: Path to the ship sensor configurations TOML file.
    deployment_label: Label of the deployment to load.

    Returns
    -------
    Resolved DeploymentConfig for the given deployment.
    """
    raw: dict[str, Any] = read_config(path)

    topside_extrinsics: dict[str, dict[str, Any]] = {
        entry["label"]: entry
        for entry in raw.get("usbl_extrinsics_profiles", [])
    }
    uncertainty_profiles: dict[str, dict[str, Any]] = {
        entry["label"]: entry
        for entry in raw.get("usbl_uncertainty_profiles", [])
    }

    deployment_entry: dict[str, Any] | None = None
    for entry in raw.get("deployment_configs", []):
        if entry["deployment_label"] == deployment_label:
            deployment_entry = entry
            break

    if deployment_entry is None:
        raise KeyError(f"deployment not found: {deployment_label!r}")

    extrinsics_label: str = deployment_entry["usbl_extrinsics_profile"]
    if extrinsics_label not in topside_extrinsics:
        raise KeyError(
            f"usbl_extrinsics_profile not found: {extrinsics_label!r}"
        )

    uncertainty_label: str = deployment_entry["usbl_uncertainty_profile"]
    if uncertainty_label not in uncertainty_profiles:
        raise KeyError(
            f"usbl_uncertainty_profile not found: {uncertainty_label!r}"
        )

    extrinsics_entry: dict[str, Any] = topside_extrinsics[extrinsics_label]
    uncertainty_entry: dict[str, Any] = uncertainty_profiles[uncertainty_label]

    usbl_modem = TopsideUsblModemConfig.model_validate(extrinsics_entry)
    usbl_uncertainty = UsblUncertaintyProfile.model_validate(uncertainty_entry)

    return DeploymentConfig(
        label=deployment_label,
        ship_name=extrinsics_entry["ship_name"],
        date=extrinsics_entry["date"],
        usbl_modem=usbl_modem,
        usbl_uncertainty=usbl_uncertainty,
        sensor_keys=tuple(deployment_entry.get("sensor_keys", [])),
    )


def read_deployment_info(path: Path) -> list[DeploymentInfo]:
    """
    Read deployment info entries from a deployments TOML file.

    Arguments
    ---------
    path: Path to the deployments TOML file.

    Returns
    -------
    List of deployment info objects.
    """
    raw: dict[str, Any] = read_config(path)
    deployments: list[DeploymentInfo] = []
    for entry in raw.get("deployments", []):
        metadata: dict[str, Any] = entry.get("metadata", {})
        # Fill defaults for missing / legacy fields so older deployment TOML
        # files that predate some fields still load, then validate.
        deployments.append(
            DeploymentInfo.model_validate(
                {
                    "deployment_label": entry["deployment_label"],
                    "deployment_datetime": entry["deployment_datetime"],
                    "deployment_platform": entry.get("deployment_platform", ""),
                    "metadata": {
                        "acfr_deployment_label": metadata[
                            "acfr_deployment_label"
                        ],
                        "acfr_campaign_label": metadata["acfr_campaign_label"],
                        "acfr_platform_label": metadata.get(
                            "acfr_platform_label", ""
                        ),
                        "origin_latitude": metadata.get("origin_latitude", 0.0),
                        "origin_longitude": metadata.get(
                            "origin_longitude", 0.0
                        ),
                        "magnetic_variation": metadata.get(
                            "magnetic_variation", 0.0
                        ),
                    },
                }
            )
        )
    return deployments


def read_deployment_descriptors(path: Path) -> list[DeploymentDescriptor]:
    """
    Read deployment descriptors from a deployments TOML file.

    Arguments
    ---------
    path: Path to the deployments TOML file.

    Returns
    -------
    List of deployment descriptors.
    """
    raw: dict[str, Any] = read_config(path)
    return [
        DeploymentDescriptor.model_validate(entry)
        for entry in raw.get("deployments", [])
    ]


def write_deployment_descriptors(
    path: Path,
    descriptors: list[DeploymentDescriptor],
) -> None:
    """
    Write deployment descriptors to a deployments TOML file.

    Curated slots that are still unfilled are omitted rather than written as
    null: TOML has no null literal, and the ``None`` defaults restore them on
    read.

    Arguments
    ---------
    path: Path to write the deployments TOML file.
    descriptors: Deployment descriptors to serialize.
    """
    path.write_bytes(
        msgspec.toml.encode(
            {
                "deployments": [
                    descriptor.model_dump(mode="python", exclude_none=True)
                    for descriptor in descriptors
                ]
            }
        )
    )


def read_deployment_catalog(path: Path) -> DeploymentCatalog:
    """
    Read the curated deployment catalog from a TOML file.

    Arguments
    ---------
    path: Path to the deployment catalog TOML file.

    Returns
    -------
    The validated deployment catalog.

    Raises
    ------
    ValidationError: If a record is malformed, a key is duplicated, or a
        cross-reference names no record.
    """
    raw: dict[str, Any] = read_config(path)
    return DeploymentCatalog.model_validate(raw)


def write_deployment_catalog(path: Path, catalog: DeploymentCatalog) -> None:
    """
    Write a deployment catalog to a TOML file.

    Emitted by hand rather than by a TOML encoder so that rotation values,
    which are stated in radians, carry their degree equivalents as trailing
    comments — the one place TOML permits a comment on a sensor entry.

    Arguments
    ---------
    path: Path to write the deployment catalog TOML file.
    catalog: Deployment catalog to serialize.
    """
    blocks: list[str] = []

    for sensor in catalog.sensors:
        blocks.append(
            "[[sensors]]\n"
            f"key = {_toml_string(sensor.key)}\n"
            f"label = {_toml_string(sensor.label)}\n"
            f"vendor = {_toml_string(sensor.vendor)}\n"
            f"product = {_toml_string(sensor.product)}\n"
            f"type = {_toml_string(sensor.type)}\n"
        )

    for platform_profile in catalog.platform_profiles:
        blocks.append(
            "[[platform_profiles]]\n"
            f"key = {_toml_string(platform_profile.key)}\n"
            f"platform_label = {_toml_string(platform_profile.platform_label)}\n"
            f"platform_class = {_toml_string(platform_profile.platform_class)}\n"
            "platform_operator = "
            f"{_toml_string(platform_profile.platform_operator)}\n"
            f"{_format_profile_sensors(platform_profile.sensors)}"
        )

    for vessel_profile in catalog.vessel_profiles:
        blocks.append(
            "[[vessel_profiles]]\n"
            f"key = {_toml_string(vessel_profile.key)}\n"
            f"vessel_name = {_toml_string(vessel_profile.vessel_name)}\n"
            f"{_format_profile_sensors(vessel_profile.sensors)}"
        )

    for platform_entry in catalog.deployment_platforms:
        blocks.append(
            "[[deployment_platforms]]\n"
            f"deployment_label = {_toml_string(platform_entry.deployment_label)}\n"
            f"platform_profile = {_toml_string(platform_entry.platform_profile)}\n"
        )

    for vessel_entry in catalog.deployment_vessels:
        blocks.append(
            "[[deployment_vessels]]\n"
            f"deployment_label = {_toml_string(vessel_entry.deployment_label)}\n"
            f"vessel_profile = {_toml_string(vessel_entry.vessel_profile)}\n"
        )

    path.write_text("\n".join(blocks))


def _toml_string(value: str) -> str:
    """Format a string as a TOML basic string."""
    return json.dumps(value)


def _format_profile_sensors(sensors: list[CatalogProfileSensor]) -> str:
    """
    Format a profile's sensor list as a multi-line TOML array.

    Each sensor is one line, so a sensor carrying a pose can be annotated with
    its rotations in degrees.
    """
    if not sensors:
        return "sensors = []\n"

    lines: list[str] = ["sensors = ["]
    for sensor in sensors:
        entry: str = (
            f"    {{ key = {_toml_string(sensor.key)}, "
            f"identity = {_toml_string(sensor.identity)}"
        )
        comment: str = ""
        if sensor.extrinsics is not None:
            pose = sensor.extrinsics
            entry += (
                f", extrinsics = {{ locx = {pose.locx!r}, "
                f"locy = {pose.locy!r}, locz = {pose.locz!r}, "
                f"rotx = {pose.rotx!r}, roty = {pose.roty!r}, "
                f"rotz = {pose.rotz!r} }}"
            )
            comment = (
                "  # rotation in degrees: "
                f"{math.degrees(pose.rotx):.3f}, "
                f"{math.degrees(pose.roty):.3f}, "
                f"{math.degrees(pose.rotz):.3f}"
            )
        entry += " },"
        lines.append(f"{entry}{comment}")
    lines.append("]\n")
    return "\n".join(lines)
