"""Pipeline wrappers around the sensor processing functions in
`afft.sensors`, translating the uniform calling convention into each
function's natural signature."""

from collections.abc import Mapping

import pandas as pd

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
    estimate_pressure_uncertainty,
)

from afft.utils.log import logger

from .processor_registry import register_processor


def _report_unmatched(
    n_unmatched: int,
    n_total: int,
    side: str,
    other_side: str,
    max_offset_ms: float,
) -> None:
    """
    Log the images discarded on one side, warning if more than 20% went.

    Arguments
    ---------
    n_unmatched: Number of images on this side with no counterpart.
    n_total: Number of images on this side before matching.
    side: Name of the side the images were discarded from.
    other_side: Name of the side they found no match on.
    max_offset_ms: Matching tolerance, quoted in the messages.
    """
    if not n_unmatched:
        return

    logger.info(
        f"dropped {n_unmatched} {side} image(s) with no {other_side} match "
        f"within {max_offset_ms} ms"
    )
    if n_unmatched / n_total > 0.20:
        logger.warning(
            f"{n_unmatched}/{n_total} {side} images "
            f"({100 * n_unmatched / n_total:.1f}%) "
            f"had no matching {other_side} image within {max_offset_ms} ms"
        )


@register_processor("pair_stereo_images", config_type=StereoPairingConfig)
def step_pair_stereo_images(
    frames: Mapping[str, pd.DataFrame],
    config: StereoPairingConfig,
) -> pd.DataFrame:
    """Pair left/right stereo captures into one frame per trigger."""
    result: StereoPairingResult = pair_stereo_images(frames["df"], config)

    _report_unmatched(
        result.left_unmatched,
        result.left_total,
        "left",
        "right",
        config.max_offset_ms,
    )
    _report_unmatched(
        result.right_unmatched,
        result.right_total,
        "right",
        "left",
        config.max_offset_ms,
    )

    return result.frame


@register_processor(
    "estimate_pressure_uncertainty", config_type=PressureUncertaintyConfig
)
def step_estimate_pressure_uncertainty(
    frames: Mapping[str, pd.DataFrame],
    config: PressureUncertaintyConfig,
) -> pd.DataFrame:
    """Add a `depth_uncertainty` column to a pressure frame."""
    return estimate_pressure_uncertainty(frames["df"], config)


@register_processor(
    "estimate_dvl_uncertainty", config_type=DvlUncertaintyConfig
)
def step_estimate_dvl_uncertainty(
    frames: Mapping[str, pd.DataFrame],
    config: DvlUncertaintyConfig,
) -> pd.DataFrame:
    """Add per-axis velocity and attitude uncertainty columns to a DVL frame."""
    return estimate_dvl_uncertainty(frames["df"], config)
