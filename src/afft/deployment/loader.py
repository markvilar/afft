"""Loaders for deployment configuration and metadata from TOML files."""

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .types import (
    DeploymentConfig,
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
