"""Module for functionality for the WorldTides API."""

import requests

import arrow
import dotenv
import pandas as pd


def get_sea_level_worldtides(
    longitude: float, latitude: float, start_date: str, end_date: str
) -> pd.DataFrame:
    """
    Get sea level data from the WorldTides API.

    Parameters:
        longitude: Longitude in decimal degrees
        latitude: Latitude in decimal degrees
        start_date: Start date in format YYYYMMDD
        end_date: End date in format YYYYMMDD
    Returns:
        DataFrame with results
    """
    assert longitude > -180 and longitude < 180, (
        f"longitude must be between -180 and 180, got: {longitude}"
    )
    assert latitude > -90 and latitude < 90, (
        f"latitude must be between -90 and 90, got: {latitude}"
    )
    assert "WORLDTIDES_API_KEY" in dotenv.dotenv_values(), (
        "missing .env value: 'WORLDTIDES_API_KEY'"
    )

    time_start: arrow.Arrow = arrow.get(start_date, "YYYYMMDD")
    time_end: arrow.Arrow = arrow.get(end_date, "YYYYMMDD")

    assert time_start < time_end, "start date must be before end date"

    url: str = "https://www.worldtides.info/api/v3"
    params: dict = {
        "heights": "",
        "date": time_start.format("YYYY-MM-DD"),
        "days": (time_end - time_start).days + 1,
        "step": 3600,  # seconds (1 hour)
        "lat": latitude,
        "lon": longitude,
        "key": dotenv.dotenv_values().get("WORLDTIDES_API_KEY"),
    }

    # NOTE: Data fields from World Tides API
    # 'status', 'callCount', 'copyright',
    # 'requestLat', 'requestLon', 'responseLat',
    # 'responseLon', 'atlas', 'station', 'heights'
    response: requests.Response = requests.get(url, params=params)
    response.raise_for_status()
    data: dict = response.json()

    # Parse data
    df: pd.DataFrame = pd.DataFrame(data["heights"])
    df["sea_level"] = df["height"]
    df["datetime"] = pd.to_datetime(df["date"])
    df: pd.DataFrame = df.drop(columns=["date", "height"])

    # Add metadata
    df["station"] = data.get("station")
    df["latitude"] = data.get("responseLat")
    df["longitude"] = data.get("responseLon")
    df["atlas"] = data.get("atlas")

    return df
