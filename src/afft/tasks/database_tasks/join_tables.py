"""Module for processing database tables."""

from dataclasses import dataclass
from typing import Callable

import polars as pl

from afft.io.sql import Endpoint, read_database
from afft.utils.log import logger
from afft.utils.result import Ok, Err, Result


@dataclass
class JoinTableConfig:
    """Class representing a task configuration."""

    label: str
    queries: dict[str, str]
    join: dict[str, str]
    selections: dict[str, list]


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

    return data_callback(dataframes)


def collect_camera_metadata(
    dataframes: dict[str, pl.DataFrame],
    selections: dict[str, list],
    base: str,
    join_on: str,
) -> pl.DataFrame:
    """Process a collection of structured data.

    :arg dataframes:    mapping from name to data frame
    :arg selections:    mapping from name to columns
    :arg base:          base data frame name for joining
    :arg join_on:       column used to join data frames
    """
    for key, data_frame in dataframes.items():
        dataframes[key] = data_frame.sort(join_on)

    for key, columns in selections.items():
        assert key in dataframes, "missing data frame key: {key}"
        dataframes[key] = dataframes.get(key).select(columns)

    left: pl.DataFrame = dataframes.pop(base)
    for key, right in dataframes.items():
        left: pl.DataFrame = left.join_asof(right, on=join_on, strategy="nearest")

    joined: pl.DataFrame = left
    return joined


DataFrameMap = dict[str, pl.DataFrame]
DataFrameProcessor = Callable[[DataFrameMap], pl.DataFrame]


def create_data_frame_processor(
    selections: dict[str, list],
    base: str,
    join_on: str,
) -> Callable:
    """Creates a table processor."""

    def table_processor(dataframes: dict[str, pl.DataFrame]) -> pl.DataFrame:
        """Processes a collection of data frames."""

        return collect_camera_metadata(dataframes, selections, base, join_on)

    return table_processor


def join_database_tables(
    endpoint: Endpoint,
    queries: dict[str, str],
    selections: dict[str, list],
    base: str,
    join_on: str,
) -> pl.DataFrame:
    """Retrieves, processes, and joins data frames from a database.

    Arguments:
     - output:      output file path
     - queries:     mapping from name to query strings
    """

    # TODO: Implement functionality to support the following operations for
    # arbitrary number of tables: sorting, selecting, smoothing, and
    # joining with a reference table

    processor: DataFrameProcessor = create_data_frame_processor(
        selections, base, join_on
    )

    return request_data_and_dispatch(
        endpoint,
        queries,
        data_callback=processor,
        error_callback=logger.error,
    )
