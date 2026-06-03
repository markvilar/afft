"""Actions for sensor-specific processing CLI commands."""

from pathlib import Path

import pandas as pd

from afft.deployment import load_deployment_config
from afft.sensors.usbl_linkquest import (
    UsblTransceiverExtrinsics,
    process_tracklink_usbl,
)
from afft.sensors.usbl_linkquest.types import (
    UsblProcessingConfig,
    UsblResolvePositionConfig,
    UsblUncertaintyConfig,
)
from afft.utils.log import logger


def dispatch_process_tracklink_usbl(
    usbl_file: str | Path,
    pressure_file: str | Path,
    output_file: str | Path,
    deployment_configs: str | Path,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL data."""
    deployment = load_deployment_config(
        Path(deployment_configs), deployment_label
    )
    logger.info(
        f"deployment {deployment.label!r}: {deployment.ship_name}, "
        f"{deployment.date}, sensor_keys={list(deployment.sensor_keys)}"
    )

    extrinsics = UsblTransceiverExtrinsics(
        x=deployment.usbl_modem.x,
        y=deployment.usbl_modem.y,
        z=deployment.usbl_modem.z,
        phi=deployment.usbl_modem.phi,
        theta=deployment.usbl_modem.theta,
        psi=deployment.usbl_modem.psi,
    )
    logger.info(
        f"USBL transceiver extrinsics: "
        f"translation=({extrinsics.x:.3f}, {extrinsics.y:.3f}, {extrinsics.z:.3f}) m, "
        f"rotation=(phi={extrinsics.phi:.4f}, theta={extrinsics.theta:.4f}, "
        f"psi={extrinsics.psi:.4f}) rad"
    )
    config = UsblProcessingConfig(
        resolve=UsblResolvePositionConfig(extrinsics=extrinsics),
        uncertainty=UsblUncertaintyConfig(
            horizontal_position_std=deployment.usbl_uncertainty.horizontal_position_std,
            depth_position_std=deployment.usbl_uncertainty.slant_range_std,
        ),
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    pressure: pd.DataFrame = pd.read_csv(Path(pressure_file))

    result: pd.DataFrame = process_tracklink_usbl(usbl, pressure, config)

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")
