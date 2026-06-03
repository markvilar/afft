"""Actions for sensor-specific processing CLI commands."""

from pathlib import Path

import pandas as pd

from afft.deployment import load_deployment_config
from afft.sensors.usbl_linkquest import parse_tracklink_log
from afft.sensors.usbl_evologics import (
    EvologicsTransceiverExtrinsics,
    process_evologics_usbl,
)
from afft.sensors.usbl_evologics.types import EvologicsProcessingConfig
from afft.sensors.usbl_linkquest import (
    TrackLinkTransceiverExtrinsics,
    process_tracklink_usbl,
)
from afft.sensors.usbl_linkquest.types import (
    TrackLinkProcessingConfig,
    TrackLinkResolvePositionConfig,
    TrackLinkUncertaintyConfig,
)
from afft.utils.log import logger


def dispatch_parse_tracklink_log(
    source_file: str | Path,
    output_file: str | Path,
) -> None:
    """Parse a merged TrackLink USBL log file and write fixes to CSV."""
    source_path = Path(source_file)
    output_path = Path(output_file)

    result: pd.DataFrame = parse_tracklink_log(source_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")


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

    extrinsics = TrackLinkTransceiverExtrinsics(
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
    config = TrackLinkProcessingConfig(
        resolve=TrackLinkResolvePositionConfig(extrinsics=extrinsics),
        uncertainty=TrackLinkUncertaintyConfig(
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


def dispatch_process_evologics_usbl(
    usbl_file: str | Path,
    output_file: str | Path,
    deployment_configs: str | Path,
    deployment_label: str,
) -> None:
    """Convert Evologics USBL data to the unified USBL output schema."""
    deployment = load_deployment_config(
        Path(deployment_configs), deployment_label
    )
    logger.info(
        f"deployment {deployment.label!r}: {deployment.ship_name}, "
        f"{deployment.date}, sensor_keys={list(deployment.sensor_keys)}"
    )

    extrinsics = EvologicsTransceiverExtrinsics(
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

    config = EvologicsProcessingConfig(
        extrinsics=extrinsics,
        horizontal_position_std=deployment.usbl_uncertainty.horizontal_position_std,
        depth_position_std=deployment.usbl_uncertainty.slant_range_std,
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    result: pd.DataFrame = process_evologics_usbl(usbl, config)

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")
