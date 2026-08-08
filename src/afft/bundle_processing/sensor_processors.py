"""Pipeline wrappers around the sensor processing functions in
`afft.sensors`, translating the uniform calling convention into each
function's natural signature."""

from collections.abc import Mapping

import pandas as pd

from afft.sensors.acfr_vision import (
    PairStereoImagesConfig,
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

from .registry import register_processor


@register_processor("pair_stereo_images", config_type=PairStereoImagesConfig)
def step_pair_stereo_images(
    frames: Mapping[str, pd.DataFrame],
    config: PairStereoImagesConfig,
) -> pd.DataFrame:
    """Pair left/right stereo captures into one frame per trigger."""
    return pair_stereo_images(frames["df"], config)


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
