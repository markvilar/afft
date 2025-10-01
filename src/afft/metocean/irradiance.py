"""Module for working with irradiance data from NASA Power API."""

import dataclasses
import requests

import pandas as pd


@dataclasses.dataclass(frozen=True)
class DownwardIrradianceRequest:
    """Class representing a request for irradiance data from the Nasa Power API."""

    latitude: float
    longitude: float
    start_date: str  # Format: YYYYMMDD
    end_date: str  # Format: YYYYMMDD


SUPPORTED_TIME_STANDARD: list[str] = ["UTC", "LST"]


def get_downward_irradiance(
    longitude: float,
    latitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Retrieve hourly all-sky surface shortwave downward irradiance (ALLSKY_SFC_SW_DWN) from NASA POWER API.

    Parameters:
        longitude: Longitude in decimal degrees.
        latitude: Latitude in decimal degrees.
        start_date: Start date, format 'YYYYMMDD'.
        end_date: End date, format 'YYYYMMDD'.

    Returns:
        pd.DataFrame: DataFrame of results.
    """
    assert longitude > -180 and longitude < 180, (
        f"longitude must be between -180 and 180, got: {longitude}"
    )
    assert latitude > -90 and latitude < 90, (
        f"latitude must be between -90 and 90, got: {latitude}"
    )

    url: str = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        f"parameters=ALLSKY_SFC_SW_DWN"
        f"&community=RE"
        f"&longitude={longitude}"
        f"&latitude={latitude}"
        f"&start={start_date}"
        f"&end={end_date}"
        f"&format=JSON"
        f"&time-standard=UTC"
    )

    response: requests.Response = requests.get(url)
    response.raise_for_status()

    # NOTE: Data keys: 'type', 'geometry', 'properties', 'header', 'messages', 'parameters', 'times'
    data: dict = response.json()

    # Parse data
    coordinates: list[float] = data["geometry"]["coordinates"]
    hourly_records: dict[str, float] = data["properties"]["parameter"][
        "ALLSKY_SFC_SW_DWN"
    ]
    rows: list[dict] = [
        {"datetime": date, "shortwave_downward_irradiance": value}
        for date, value in hourly_records.items()
    ]

    df: pd.DataFrame = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d%H")
    df["longitude"] = coordinates[0]
    df["latitude"] = coordinates[1]
    df["height"] = coordinates[2]
    df["time_standard"] = "UTC"
    df["irradiance_unit"] = "Wh/m2"

    return df


def request_downward_irradiance(
    request: DownwardIrradianceRequest,
) -> pd.DataFrame:
    """Request hourly shortwave downward irradiance from the NASA Power API."""
    return get_downward_irradiance(
        longitude=request.longitude,
        latitude=request.latitude,
        start_date=request.start_date,
        end_date=request.end_date,
    )
