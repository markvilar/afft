"""Reader and writer for the curated deployment catalog TOML file."""

import json
import math

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .catalog_types import CatalogProfileSensor, DeploymentCatalog


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

    Emitted by hand rather than by a TOML encoder so that rotations, stated in
    radians, carry their degree equivalents as trailing comments. The mapping
    tables are sorted by deployment label; the record tables keep the order
    they are held in, since a curated file orders those deliberately.

    Arguments
    ---------
    path: Path to write the deployment catalog TOML file.
    catalog: Deployment catalog to serialize.
    """
    blocks: list[str] = []

    for sensor in catalog.sensor_identities:
        blocks.append(
            "[[sensor_identities]]\n"
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

    for platform_entry in sorted(
        catalog.deployment_platforms,
        key=lambda entry: entry.deployment_label,
    ):
        blocks.append(
            "[[deployment_platforms]]\n"
            f"deployment_label = {_toml_string(platform_entry.deployment_label)}\n"
            f"platform_profile = {_toml_string(platform_entry.platform_profile)}\n"
        )

    for vessel_entry in sorted(
        catalog.deployment_vessels,
        key=lambda entry: entry.deployment_label,
    ):
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
        topics: str = ", ".join(
            _toml_string(topic) for topic in sensor.message_topics
        )
        entry: str = (
            f"    {{ key = {_toml_string(sensor.key)}, "
            f"message_topics = [{topics}]"
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
