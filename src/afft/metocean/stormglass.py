"""Module for functionality for the Stormglass API."""

import requests

import arrow
import dotenv
import pandas as pd


def get_sea_level_stormglass(
    longitude: float, latitude: float, start_date: str, end_date: str
) -> pd.DataFrame:
    """
    Get sea level from the Stormglass API.

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
    assert "STORMGLASS_API_KEY" in dotenv.dotenv_values(), (
        "missing .env value: 'STORMGLASS_API_KEY'"
    )

    start_time: arrow.Arrow = arrow.get(start_date, "YYYYMMDD")
    end_time: arrow.Arrow = arrow.get(end_date, "YYYYMMDD")

    response: requests.Response = requests.get(
        "https://api.stormglass.io/v2/tide/sea-level/point",
        params={
            "lng": longitude,
            "lat": latitude,
            "start": start_time.to("UTC").timestamp(),
            "end": end_time.to("UTC").timestamp(),
        },
        headers={
            "Authorization": dotenv.dotenv_values().get("STORMGLASS_API_KEY")
        },
    )

    response.raise_for_status()
    data: dict = response.json()

    # Parse data
    df: pd.DataFrame = _tabulate_reponse_stormglass(data)
    df["sea_level"] = df["sg"]
    df["datetime"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["sg", "time"])

    return df


def _tabulate_reponse_stormglass(response: dict) -> pd.DataFrame:
    """Converts a Stormglass reponse to a data frame."""
    df: pd.DataFrame = pd.DataFrame(response.get("data"))
    metadata: dict = _format_sealevel_response_metadata(response.get("meta"))
    for key, value in metadata.items():
        df[key] = value
    return df


def _format_sealevel_response_metadata(metadata: dict) -> dict:
    """Formats the metadata of a Stormglass response."""
    station: dict = metadata.get("station")
    station_metadata: dict = {
        "longitude": station.get("lng"),
        "latitude": station.get("lat"),
        "distance": station.get("distance"),
        "name": station.get("name"),
        "source": station.get("source"),
    }
    request_metadata: dict = {
        "longitude": metadata.get("lng"),
        "latitude": metadata.get("lat"),
        "datum": metadata.get("datum"),
        "start": metadata.get("start"),
        "end": metadata.get("end"),
    }

    merged: dict = dict()
    for key, value in request_metadata.items():
        merged[f"request_{key}"] = value

    for key, value in station_metadata.items():
        merged[f"station_{key}"] = value

    return merged
