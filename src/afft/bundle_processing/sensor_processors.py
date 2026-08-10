"""Pipeline wrappers around the sensor processing functions in
`afft.sensors`, translating the uniform calling convention into each
function's natural signature."""

from collections.abc import Mapping
from typing import TypeVar

import pandas as pd

from pydantic import BaseModel, ValidationError

from afft.sensors.acfr_vision import (
    StereoPairingConfig,
    StereoPairingResult,
    pair_stereo_images,
)
from afft.sensors.dvl_teledyne import (
    DvlUncertaintyConfig,
    estimate_dvl_uncertainty,
)
from afft.sensors.pressure_parosci import (
    PressureUncertaintyConfig,
    SeaLevelCorrectionConfig,
    correct_pressure_for_sea_level,
    estimate_pressure_uncertainty,
)
from afft.sensors.usbl_evologics import (
    EvologicsProcessingConfig,
    EvologicsTransceiverExtrinsics,
    process_evologics_usbl,
)
from afft.sensors.usbl_linkquest import (
    TrackLinkProcessingFromMessagesConfig,
    TrackLinkTransceiverExtrinsics,
    process_tracklink_usbl_from_messages,
)
from afft.utils.log import logger

from .processor_registry import register_processor

Extrinsics = TypeVar("Extrinsics", bound=BaseModel)


def _decode_extrinsics(
    frames: Mapping[str, pd.DataFrame],
    extrinsics_type: type[Extrinsics],
    processor_key: str,
) -> Extrinsics | None:
    """
    Decode the one-row extrinsics frame into `extrinsics_type`.

    Absence of the `extrinsics` input is the signal to run without an
    extrinsics correction, for deployments whose readings were already
    corrected upstream. Which of the two happened is logged, since a mistyped
    input key is indistinguishable from a deliberate omission.

    The decode is strict. A frame that is empty, holds more than one row, or
    does not carry exactly the expected fields means the bundle was built
    wrong, and taking the first row regardless would shift every resulting
    position by a plausible-looking amount.

    Arguments
    ---------
    frames: The step's inputs, keyed by processor argument name.
    extrinsics_type: The sensor's extrinsics model.
    processor_key: Registered processor name, for the log lines.

    Returns
    -------
    The decoded extrinsics, or None when the input was not supplied.

    Raises
    ------
    ValueError: If the frame does not hold exactly one row, or its columns do
        not match `extrinsics_type`.
    """
    frame: pd.DataFrame | None = frames.get("extrinsics")
    if frame is None:
        logger.info(
            f"{processor_key}: no extrinsics input; running without an "
            f"extrinsics correction"
        )
        return None

    if len(frame) != 1:
        raise ValueError(
            f"{processor_key}: extrinsics frame holds {len(frame)} rows, "
            f"expected exactly 1"
        )

    # Every field carries a default, so a frame missing a column would
    # otherwise decode to a silent zero for that axis.
    expected: set[str] = set(extrinsics_type.model_fields)
    if set(frame.columns) != expected:
        raise ValueError(
            f"{processor_key}: extrinsics frame does not match "
            f"{extrinsics_type.__name__}: columns are "
            f"{sorted(frame.columns)}, expected {sorted(expected)}"
        )

    try:
        extrinsics: Extrinsics = extrinsics_type(**frame.iloc[0].to_dict())
    except ValidationError as error:
        raise ValueError(
            f"{processor_key}: extrinsics frame does not match "
            f"{extrinsics_type.__name__}: {error}"
        ) from error

    logger.info(f"{processor_key}: applying extrinsics from the bundle")
    return extrinsics


@register_processor("pair_stereo_images", config_type=StereoPairingConfig)
def step_pair_stereo_images(
    frames: Mapping[str, pd.DataFrame],
    config: StereoPairingConfig,
) -> pd.DataFrame:
    """Pair left/right stereo captures into one frame per trigger."""
    result: StereoPairingResult = pair_stereo_images(frames["images"], config)
    return result.frame


@register_processor(
    "estimate_pressure_uncertainty", config_type=PressureUncertaintyConfig
)
def step_estimate_pressure_uncertainty(
    frames: Mapping[str, pd.DataFrame],
    config: PressureUncertaintyConfig,
) -> pd.DataFrame:
    """Add a `depth_uncertainty` column to a pressure frame."""
    return estimate_pressure_uncertainty(frames["pressure"], config)


@register_processor(
    "correct_pressure_for_sea_level", config_type=SeaLevelCorrectionConfig
)
def step_correct_pressure_for_sea_level(
    frames: Mapping[str, pd.DataFrame],
    config: SeaLevelCorrectionConfig,
) -> pd.DataFrame:
    """Subtract the interpolated tide from a pressure frame's depth, with
    the convention `corrected_depth = depth - sea_level`."""
    return correct_pressure_for_sea_level(
        frames["pressure"], frames["sea_level"], config
    )


@register_processor(
    "estimate_dvl_uncertainty", config_type=DvlUncertaintyConfig
)
def step_estimate_dvl_uncertainty(
    frames: Mapping[str, pd.DataFrame],
    config: DvlUncertaintyConfig,
) -> pd.DataFrame:
    """Add per-axis velocity and attitude uncertainty columns to a DVL frame."""
    return estimate_dvl_uncertainty(frames["dvl"], config)


@register_processor(
    "process_tracklink_usbl_from_messages",
    config_type=TrackLinkProcessingFromMessagesConfig,
)
def step_process_tracklink_usbl(
    frames: Mapping[str, pd.DataFrame],
    config: TrackLinkProcessingFromMessagesConfig,
) -> pd.DataFrame:
    """Resolve TrackLink USBL positions, correcting for the transceiver
    extrinsics the bundle carries."""
    extrinsics: TrackLinkTransceiverExtrinsics | None = _decode_extrinsics(
        frames,
        TrackLinkTransceiverExtrinsics,
        "process_tracklink_usbl_from_messages",
    )
    return process_tracklink_usbl_from_messages(
        frames["usbl"], frames["pressure"], extrinsics, config
    )


@register_processor(
    "process_evologics_usbl", config_type=EvologicsProcessingConfig
)
def step_process_evologics_usbl(
    frames: Mapping[str, pd.DataFrame],
    config: EvologicsProcessingConfig,
) -> pd.DataFrame:
    """Resolve Evologics USBL positions, correcting for the transceiver
    extrinsics the bundle carries."""
    extrinsics: EvologicsTransceiverExtrinsics | None = _decode_extrinsics(
        frames, EvologicsTransceiverExtrinsics, "process_evologics_usbl"
    )
    return process_evologics_usbl(frames["usbl"], extrinsics, config)
