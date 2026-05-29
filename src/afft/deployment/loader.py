"""Loader for deployment configuration from TOML files."""

from pathlib import Path

from afft.io.config_io import read_config

from .types import DeploymentConfig, TopsideUsblModemConfig


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
    raw: dict = read_config(path)

    sensor_configs: dict[str, dict] = {
        entry["label"]: entry for entry in raw.get("ship_sensor_configs", [])
    }

    deployment_entry: dict | None = None
    for entry in raw.get("deployment_configs", []):
        if entry["deployment_label"] == deployment_label:
            deployment_entry = entry
            break

    if deployment_entry is None:
        raise KeyError(f"deployment not found: {deployment_label!r}")

    config_label: str = deployment_entry["ship_sensor_config"]
    if config_label not in sensor_configs:
        raise KeyError(f"ship sensor config not found: {config_label!r}")

    sensor_config: dict = sensor_configs[config_label]

    usbl_modem = TopsideUsblModemConfig(
        x=sensor_config["x"],
        y=sensor_config["y"],
        z=sensor_config["z"],
        phi=sensor_config["phi"],
        theta=sensor_config["theta"],
        psi=sensor_config["psi"],
        comment=sensor_config.get("comment", ""),
    )

    return DeploymentConfig(
        label=deployment_label,
        ship_name=sensor_config["ship_name"],
        date=sensor_config["date"],
        usbl_modem=usbl_modem,
        sensor_keys=tuple(deployment_entry.get("sensor_keys", [])),
    )
