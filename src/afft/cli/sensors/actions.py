"""Actions for sensor-specific processing CLI commands."""

from pathlib import Path

import pandas as pd

from afft.deployment import DeploymentDescriptor, VesselSensor
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
from afft.tasks.build_deployment_bundle import load_target_descriptor
from afft.utils.log import logger


def _find_vessel_sensor(
    descriptor: DeploymentDescriptor,
    sensor_key: str,
) -> VesselSensor:
    """Find a vessel sensor on a descriptor by its catalog key."""
    for sensor in descriptor.vessel.sensors:
        if sensor.key == sensor_key:
            return sensor

    raise ValueError(
        f"deployment {descriptor.deployment_label!r} has no vessel sensor "
        f"{sensor_key!r}"
    )


def invoke_parse_tracklink_log(
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


def invoke_process_tracklink_usbl_from_messages(
    usbl_file: str | Path,
    pressure_file: str | Path,
    output_file: str | Path,
    descriptor_file: str | Path,
    deployment_label: str,
    ignore_extrinsics: bool = False,
    horizontal_position_std: float | None = None,
    depth_position_std: float | None = None,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink AUV messages."""
    descriptor = load_target_descriptor(Path(descriptor_file), deployment_label)
    logger.info(f"deployment {descriptor.deployment_label!r}")

    extrinsics: TrackLinkTransceiverExtrinsics | None
    if ignore_extrinsics:
        extrinsics = None
        logger.info("USBL transceiver extrinsics: ignored (zero extrinsics)")
    else:
        sensor = _find_vessel_sensor(descriptor, "usbl_linkquest_transceiver")
        if sensor.extrinsics is None:
            raise ValueError(
                f"deployment {descriptor.deployment_label!r} has no "
                f"extrinsics for usbl_linkquest_transceiver"
            )
        extrinsics = TrackLinkTransceiverExtrinsics(
            locx=sensor.extrinsics.locx,
            locy=sensor.extrinsics.locy,
            locz=sensor.extrinsics.locz,
            rotx=sensor.extrinsics.rotx,
            roty=sensor.extrinsics.roty,
            rotz=sensor.extrinsics.rotz,
        )
        logger.info(
            f"USBL transceiver extrinsics: "
            f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
            f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
            f"rotz={extrinsics.rotz:.4f}) rad"
        )
    uncertainty_kwargs: dict[str, float] = {}
    if horizontal_position_std is not None:
        uncertainty_kwargs["horizontal_position_std"] = horizontal_position_std
    if depth_position_std is not None:
        uncertainty_kwargs["depth_position_std"] = depth_position_std
    config = TrackLinkProcessingFromMessagesConfig(
        resolve=TrackLinkResolvePositionFromMessagesConfig(),
        uncertainty=TrackLinkUncertaintyConfig(**uncertainty_kwargs),
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    pressure: pd.DataFrame = pd.read_csv(Path(pressure_file))

    result: pd.DataFrame = process_tracklink_usbl_from_messages(
        usbl, pressure, extrinsics, config
    )

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")


def invoke_process_tracklink_usbl_from_logs(
    usbl_file: str | Path,
    output_file: str | Path,
    descriptor_file: str | Path,
    deployment_label: str,
    ignore_extrinsics: bool = False,
    horizontal_position_std: float | None = None,
    depth_position_std: float | None = None,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL log entries."""
    descriptor = load_target_descriptor(Path(descriptor_file), deployment_label)
    logger.info(f"deployment {descriptor.deployment_label!r}")

    extrinsics: TrackLinkTransceiverExtrinsics | None
    if ignore_extrinsics:
        extrinsics = None
        logger.info("USBL transceiver extrinsics: ignored (zero extrinsics)")
    else:
        sensor = _find_vessel_sensor(descriptor, "usbl_linkquest_transceiver")
        if sensor.extrinsics is None:
            raise ValueError(
                f"deployment {descriptor.deployment_label!r} has no "
                f"extrinsics for usbl_linkquest_transceiver"
            )
        extrinsics = TrackLinkTransceiverExtrinsics(
            locx=sensor.extrinsics.locx,
            locy=sensor.extrinsics.locy,
            locz=sensor.extrinsics.locz,
            rotx=sensor.extrinsics.rotx,
            roty=sensor.extrinsics.roty,
            rotz=sensor.extrinsics.rotz,
        )
        logger.info(
            f"USBL transceiver extrinsics: "
            f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
            f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
            f"rotz={extrinsics.rotz:.4f}) rad"
        )
    uncertainty_kwargs: dict[str, float] = {}
    if horizontal_position_std is not None:
        uncertainty_kwargs["horizontal_position_std"] = horizontal_position_std
    if depth_position_std is not None:
        uncertainty_kwargs["depth_position_std"] = depth_position_std
    config = TrackLinkProcessingFromLogsConfig(
        resolve=TrackLinkResolvePositionFromLogsConfig(),
        uncertainty=TrackLinkUncertaintyConfig(**uncertainty_kwargs),
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))

    try:
        result: pd.DataFrame = process_tracklink_usbl_from_logs(
            usbl, extrinsics, config
        )
    except ValueError as error:
        logger.error(f"skipping {Path(usbl_file).name}: {error}")
        return

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")


def invoke_process_evologics_usbl(
    usbl_file: str | Path,
    output_file: str | Path,
    descriptor_file: str | Path,
    deployment_label: str,
    ignore_extrinsics: bool = False,
    horizontal_position_std: float | None = None,
    depth_position_std: float | None = None,
) -> None:
    """Convert Evologics USBL data to the USBL output schema."""
    descriptor = load_target_descriptor(Path(descriptor_file), deployment_label)
    logger.info(f"deployment {descriptor.deployment_label!r}")

    extrinsics: EvologicsTransceiverExtrinsics | None
    if ignore_extrinsics:
        extrinsics = None
        logger.info("USBL transceiver extrinsics: ignored (zero extrinsics)")
    else:
        sensor = _find_vessel_sensor(descriptor, "usbl_evologics_transceiver")
        if sensor.extrinsics is None:
            raise ValueError(
                f"deployment {descriptor.deployment_label!r} has no "
                f"extrinsics for usbl_evologics_transceiver"
            )
        extrinsics = EvologicsTransceiverExtrinsics(
            locx=sensor.extrinsics.locx,
            locy=sensor.extrinsics.locy,
            locz=sensor.extrinsics.locz,
            rotx=sensor.extrinsics.rotx,
            roty=sensor.extrinsics.roty,
            rotz=sensor.extrinsics.rotz,
        )
        logger.info(
            f"USBL transceiver extrinsics: "
            f"translation=({extrinsics.locx:.3f}, {extrinsics.locy:.3f}, {extrinsics.locz:.3f}) m, "
            f"rotation=(rotx={extrinsics.rotx:.4f}, roty={extrinsics.roty:.4f}, "
            f"rotz={extrinsics.rotz:.4f}) rad"
        )

    uncertainty_kwargs: dict[str, float] = {}
    if horizontal_position_std is not None:
        uncertainty_kwargs["horizontal_position_std"] = horizontal_position_std
    if depth_position_std is not None:
        uncertainty_kwargs["depth_position_std"] = depth_position_std
    config = EvologicsProcessingConfig(**uncertainty_kwargs)

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    result: pd.DataFrame = process_evologics_usbl(usbl, extrinsics, config)

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")
