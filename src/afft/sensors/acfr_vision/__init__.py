"""ACFR vision system sensor processing."""

from afft.sensors.registry import register_sensor

from .processors import pair_stereo_images as pair_stereo_images
from .types import PairStereoImagesConfig as PairStereoImagesConfig

register_sensor("acfr_vision", PairStereoImagesConfig, pair_stereo_images)
