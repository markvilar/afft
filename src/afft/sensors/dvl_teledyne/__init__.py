"""Teledyne DVL sensor processing."""

from afft.sensors.registry import register_sensor

from .processors import estimate_dvl_uncertainty as estimate_dvl_uncertainty
from .types import DvlUncertaintyConfig as DvlUncertaintyConfig

register_sensor("dvl_teledyne", DvlUncertaintyConfig, estimate_dvl_uncertainty)
