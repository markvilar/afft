"""Module with functionality to obtain solar zenith angles using NASAs POWER API."""

import requests

import arrow
import pandas as pd


def get_solar_zenith_angle(
    longitude: float,
    latitude: float,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Retrieve hourly solar zenith angle data from the NASA Power API for a given location and date range.

    Args:
        longitude (float): Longitude of the location.
        latitude (float): Latitude of the location.
        start_date (str): Start date in 'YYYYMMDD' format.
        end_date (str): End date in 'YYYYMMDD' format.

    Returns:
        pd.DataFrame of results.
    """
    assert longitude > -180 and longitude < 180, (
        f"longitude must be between -180 and 180, got: {longitude}"
    )
    assert latitude > -90 and latitude < 90, (
        f"latitude must be between -90 and 90, got: {latitude}"
    )

    time_start: arrow.Arrow = arrow.get(start_date, "YYYYMMDD")
    time_end: arrow.Arrow = arrow.get(end_date, "YYYYMMDD")

    assert time_start < time_end, "start time must be before end time"

    url: str = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        f"?parameters=SZA"
        f"&start={start_date}"
        f"&end={end_date}"
        f"&longitude={longitude}"
        f"&latitude={latitude}"
        f"&community=SB"
        f"&format=JSON"
        f"&time-standard=UTC"
    )
    response: requests.Response = requests.get(url)
    response.raise_for_status()

    # NOTE: Data keys: 'type', 'geometry', 'properties', 'header', 'messages', 'parameters', 'times'
    data: dict = response.json()

    coordinates: list[float] = data["geometry"]["coordinates"]
    hourly_records: dict[str, float] = data["properties"]["parameter"]["SZA"]
    rows: list[dict] = [
        {"datetime": date, "solar_zenthic_angle": value}
        for date, value in hourly_records.items()
    ]

    df: pd.DataFrame = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d%H")
    df["longitude"] = coordinates[0]
    df["latitude"] = coordinates[1]
    df["height"] = coordinates[2]
    df["time_standard"] = "UTC"
    df["angle_unit"] = "degrees"

    return df
