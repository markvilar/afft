"""Reader and writer for the deployment descriptors TOML file."""

import msgspec

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config

from .descriptor import DeploymentDescriptor


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

    Unfilled curated slots are omitted rather than written as null: TOML has no
    null literal, and the ``None`` defaults restore them on read.

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
