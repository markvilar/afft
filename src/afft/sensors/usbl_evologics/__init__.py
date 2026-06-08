"""Processing package for the Evologics S2C R 18/34 USBL."""

from afft.sensors.registry import register_sensor

from .processors import process_evologics_usbl as process_evologics_usbl
from .types import EvologicsProcessingConfig as EvologicsProcessingConfig
from .types import (
    EvologicsTransceiverExtrinsics as EvologicsTransceiverExtrinsics,
)

register_sensor(
    "usbl_evologics", EvologicsProcessingConfig, process_evologics_usbl
)
