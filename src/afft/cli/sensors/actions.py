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
    process_tracklink_usbl_from_logs,
    process_tracklink_usbl_from_messages,
)
from afft.sensors.usbl_linkquest.types import (
    TrackLinkProcessingFromLogsConfig,
    TrackLinkProcessingFromMessagesConfig,
    TrackLinkResolvePositionFromLogsConfig,
    TrackLinkResolvePositionFromMessagesConfig,
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


def dispatch_process_tracklink_usbl_from_messages(
    usbl_file: str | Path,
    pressure_file: str | Path,
    output_file: str | Path,
    deployment_configs: str | Path,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink AUV messages."""
    deployment = load_deployment_config(
        Path(deployment_configs), deployment_label
    )
    logger.info(
        f"deployment {deployment.label!r}: {deployment.ship_name}, "
        f"{deployment.date}, sensor_keys={list(deployment.sensor_keys)}"
    )

    extrinsics = TrackLinkTransceiverExtrinsics(
        locx=deployment.usbl_modem.locx,
        locy=deployment.usbl_modem.locy,
        locz=deployment.usbl_modem.locz,
        rotx=deployment.usbl_modem.rotx,
        roty=deployment.usbl_modem.roty,
        rotz=deployment.usbl_modem.rotz,
    )
    logger.info(
        f"USBL transceiver extrinsics: "
        f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
        f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
        f"rotz={extrinsics.rotz:.4f}) rad"
    )
    config = TrackLinkProcessingFromMessagesConfig(
        resolve=TrackLinkResolvePositionFromMessagesConfig(
            extrinsics=extrinsics
        ),
        uncertainty=TrackLinkUncertaintyConfig(
            horizontal_position_std=deployment.usbl_uncertainty.horizontal_position_std,
            depth_position_std=deployment.usbl_uncertainty.slant_range_std,
        ),
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    pressure: pd.DataFrame = pd.read_csv(Path(pressure_file))

    result: pd.DataFrame = process_tracklink_usbl_from_messages(
        usbl, pressure, config
    )

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")


def dispatch_process_tracklink_usbl_from_logs(
    usbl_file: str | Path,
    output_file: str | Path,
    deployment_configs: str | Path,
    deployment_label: str,
    ignore_extrinsics: bool = False,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL log entries."""
    deployment = load_deployment_config(
        Path(deployment_configs), deployment_label
    )
    logger.info(
        f"deployment {deployment.label!r}: {deployment.ship_name}, "
        f"{deployment.date}, sensor_keys={list(deployment.sensor_keys)}"
    )

    if ignore_extrinsics:
        extrinsics = TrackLinkTransceiverExtrinsics()
        logger.info("USBL transceiver extrinsics: ignored (zero extrinsics)")
    else:
        extrinsics = TrackLinkTransceiverExtrinsics(
            locx=deployment.usbl_modem.locx,
            locy=deployment.usbl_modem.locy,
            locz=deployment.usbl_modem.locz,
            rotx=deployment.usbl_modem.rotx,
            roty=deployment.usbl_modem.roty,
            rotz=deployment.usbl_modem.rotz,
        )
        logger.info(
            f"USBL transceiver extrinsics: "
            f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
            f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
            f"rotz={extrinsics.rotz:.4f}) rad"
        )
    config = TrackLinkProcessingFromLogsConfig(
        resolve=TrackLinkResolvePositionFromLogsConfig(extrinsics=extrinsics),
        uncertainty=TrackLinkUncertaintyConfig(
            horizontal_position_std=deployment.usbl_uncertainty.horizontal_position_std,
            depth_position_std=deployment.usbl_uncertainty.slant_range_std,
        ),
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))

    try:
        result: pd.DataFrame = process_tracklink_usbl_from_logs(usbl, config)
    except ValueError as error:
        logger.error(f"skipping {Path(usbl_file).name}: {error}")
        return

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
        locx=deployment.usbl_modem.locx,
        locy=deployment.usbl_modem.locy,
        locz=deployment.usbl_modem.locz,
        rotx=deployment.usbl_modem.rotx,
        roty=deployment.usbl_modem.roty,
        rotz=deployment.usbl_modem.rotz,
    )
    logger.info(
        f"USBL transceiver extrinsics: "
        f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
        f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
        f"rotz={extrinsics.rotz:.4f}) rad"
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
