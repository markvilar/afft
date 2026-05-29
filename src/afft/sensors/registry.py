"""Sensor registry mapping sensor keys to processing config types and processors."""

from dataclasses import dataclass
from typing import Callable

import pandas as pd

type SensorProcessor = Callable[..., pd.DataFrame]


@dataclass(slots=True, frozen=True)
class SensorRegistration:
    """
    Registry entry for a sensor type.

    Attributes
    ----------
    config_type: Dataclass type used to configure the sensor processor.
    processor: Processing function for this sensor type.
    """

    config_type: type
    processor: SensorProcessor


_SENSOR_REGISTRY: dict[str, SensorRegistration] = {}


def register_sensor(
    key: str,
    config_type: type,
    processor: SensorProcessor,
) -> None:
    """Register a sensor key with its config type and processor function."""
    _SENSOR_REGISTRY[key] = SensorRegistration(
        config_type=config_type,
        processor=processor,
    )


def get_sensor_registration(key: str) -> SensorRegistration:
    """Look up a sensor registration by key.

    Arguments
    ---------
    key: Sensor key to look up.

    Returns
    -------
    SensorRegistration for the given key.
    """
    if key not in _SENSOR_REGISTRY:
        raise KeyError(f"unknown sensor key: {key!r}")
    return _SENSOR_REGISTRY[key]
