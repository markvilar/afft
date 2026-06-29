"""Loaders for deployment configuration and metadata from TOML files."""

import msgspec

from dataclasses import asdict
from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .types import (
    DeploymentConfig,
    DeploymentInfo,
    DeploymentMetadata,
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

    usbl_modem = TopsideUsblModemConfig(
        locx=extrinsics_entry["locx"],
        locy=extrinsics_entry["locy"],
        locz=extrinsics_entry["locz"],
        rotx=extrinsics_entry["rotx"],
        roty=extrinsics_entry["roty"],
        rotz=extrinsics_entry["rotz"],
        comment=extrinsics_entry.get("comment", ""),
    )

    usbl_uncertainty = UsblUncertaintyProfile(
        horizontal_position_std=uncertainty_entry["horizontal_position_std"],
        slant_range_std=uncertainty_entry["slant_range_std"],
        bearing_std=uncertainty_entry["bearing_std"],
        ship_x_std=uncertainty_entry["ship_x_std"],
        ship_y_std=uncertainty_entry["ship_y_std"],
        ship_z_std=uncertainty_entry["ship_z_std"],
        ship_heading_std=uncertainty_entry["ship_heading_std"],
        ship_roll_std=uncertainty_entry["ship_roll_std"],
        ship_pitch_std=uncertainty_entry["ship_pitch_std"],
    )

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
        deployments.append(
            DeploymentInfo(
                deployment_label=entry["deployment_label"],
                deployment_datetime=entry["deployment_datetime"],
                deployment_platform=entry.get("deployment_platform", ""),
                metadata=DeploymentMetadata(
                    acfr_deployment_label=metadata["acfr_deployment_label"],
                    acfr_campaign_label=metadata["acfr_campaign_label"],
                    acfr_platform_label=metadata.get("acfr_platform_label", ""),
                    origin_latitude=metadata.get("origin_latitude", 0.0),
                    origin_longitude=metadata.get("origin_longitude", 0.0),
                    magnetic_variation=metadata.get("magnetic_variation", 0.0),
                    message_topics=metadata.get("message_topics", []),
                    renav_labels=metadata.get("renav_labels", []),
                    camera_calibration_files=metadata.get(
                        "camera_calibration_files", []
                    ),
                ),
            )
        )
    return deployments


def write_deployment_info(
    path: Path,
    deployments: list[DeploymentInfo],
) -> None:
    """
    Write deployment info entries to a deployments TOML file.

    Arguments
    ---------
    path: Path to write the deployments TOML file.
    deployments: Deployment info objects to serialize.
    """
    path.write_bytes(
        msgspec.toml.encode({"deployments": [asdict(d) for d in deployments]})
    )
