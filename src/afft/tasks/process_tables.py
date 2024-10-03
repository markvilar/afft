"""Module for processing database tables."""

from typing import Callable

import polars as pl

from ..io.sql import Endpoint, read_database
from ..utils.log import logger
from ..utils.result import Ok, Err, Result


def request_data_and_dispatch(
    endpoint: Endpoint,
    queries: dict[str, str],
    data_callback: Callable[[dict], pl.DataFrame],
    error_callback: Callable[[str], None],
) -> None:
    """Request data from an endpoint."""

    read_results: dict[str, Result] = {
        name: read_database(endpoint, query) for name, query in queries.items()
    }

    dataframes: dict[str, pl.DataFrame] = dict()
    for name, result in read_results.items():
        match result:
            case Ok(dataframe):
                dataframes[name] = dataframe
            case Err(message):
                error_callback(message)

    return data_callback(**dataframes)


def collect_camera_metadata(
    image: pl.DataFrame,
    ctd: pl.DataFrame,
    dvl: pl.DataFrame,
    pressure: pl.DataFrame,
) -> pl.DataFrame:
    """Process a collection of structured data."""

    # Sort data by timestamp
    ctd: pl.DataFrame = ctd.sort("timestamp")
    dvl: pl.DataFrame = dvl.sort("timestamp")
    image: pl.DataFrame = image.sort("timestamp")
    pressure: pl.DataFrame = pressure.sort("timestamp")

    # Select the relevant columns
    ctd: pl.DataFrame = ctd.select(
        ["timestamp", "conductivity", "temperature", "salinity"]
    )
    dvl: pl.DataFrame = dvl.select(["timestamp", "altitude"])
    image: pl.DataFrame = image.select(
        ["timestamp", "label", "trigger_time", "exposure_logged", "exposure"]
    )
    pressure: pl.DataFrame = pressure.select(["timestamp", "depth"])

    # TODO: Smooth data columns: CTD, DVL, pressure
    # df = df.with_columns(
    #     pl.col("your_column").rolling_mean(window_size=5).alias("smoothed_column")
    # )

    # Get the relevant columns from the image data
    camera_data: pl.DataFrame = image

    # Merge with CTD, DVL, and pressure
    for dataframe in [ctd, dvl, pressure]:
        camera_data: pl.DataFrame = camera_data.join_asof(
            dataframe,
            left_on="timestamp",
            right_on="timestamp",
            strategy="nearest",
        )

    return camera_data


def process_database_tables(
    endpoint: Endpoint,
    queries: dict[str, str],
    base: str,
) -> pl.DataFrame:
    """Retrieves, processes, and joins data frames from a database.

    Arguments:
     - output:      output file path
     - queries:     mapping from name to query strings
    """

    # TODO: Implement functionality to support the following operations for
    # arbitrary number of tables: sorting, selecting, smoothing, and
    # joining with a reference table

    return request_data_and_dispatch(
        endpoint,
        queries,
        data_callback=collect_camera_metadata,
        error_callback=logger.error,
    )
