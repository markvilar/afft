"""Module with functionality for retrieving sealevel from the Stormglass API."""

import dataclasses
import enum

import pandas as pd

from .stormglass import get_sea_level_stormglass
from .worldtides import get_sea_level_worldtides


class SeaLevelAPI(enum.StrEnum):
    """String enum for sea level APIs."""

    STORMGLASS = enum.auto()
    WORLDTIDES = enum.auto()


@dataclasses.dataclass(frozen=True)
class SeaLevelRequest:
    """Class representing a sea level request."""

    longitude: float
    latitude: float
    start_date: str  # format YYYYMMDD
    end_date: str  # format YYYYMMDD

    api: SeaLevelAPI = dataclasses.field(default=SeaLevelAPI.STORMGLASS)


def request_sea_level(request: SeaLevelRequest) -> pd.DataFrame:
    """Requests sea level from one of the APIs."""
    match request.api:
        case SeaLevelAPI.STORMGLASS:
            return request_sea_level_stormglass(request)
        case SeaLevelAPI.WORLDTIDES:
            return request_sea_level_worldtides(request)
        case _:
            raise NotImplementedError(f"invalid sea level api: {request.api}")


def get_sea_level(
    longitude: float,
    latitude: float,
    start_date: str,
    end_date: str,
    api: SeaLevelAPI = SeaLevelAPI.STORMGLASS,
) -> pd.DataFrame:
    """Gets sea level from one the APIs."""
    match api:
        case SeaLevelAPI.STORMGLASS:
            return get_sea_level_stormglass(
                longitude, latitude, start_date, end_date
            )
        case SeaLevelAPI.WORLDTIDES:
            return get_sea_level_worldtides(
                longitude, latitude, start_date, end_date
            )
        case _:
            raise NotImplementedError(f"invalid sea level api: {api}")


def request_sea_level_stormglass(request: SeaLevelRequest) -> pd.DataFrame:
    """Requests hourly sea level data from the Stormglass API."""
    return get_sea_level_stormglass(
        request.longitude,
        request.latitude,
        request.start_date,
        request.end_date,
    )


def request_sea_level_worldtides(request: SeaLevelRequest) -> pd.DataFrame:
    """Requests hourly sea level data from the WorldTides API."""
    return get_sea_level_worldtides(
        request.longitude,
        request.latitude,
        request.start_date,
        request.end_date,
    )
