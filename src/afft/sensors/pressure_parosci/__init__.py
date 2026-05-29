"""Paroscientific pressure sensor processing."""

from afft.sensors.registry import register_sensor

from .processors import (
    estimate_pressure_uncertainty as estimate_pressure_uncertainty,
)
from .types import PressureUncertaintyConfig as PressureUncertaintyConfig

register_sensor(
    "pressure_parosci", PressureUncertaintyConfig, estimate_pressure_uncertainty
)
