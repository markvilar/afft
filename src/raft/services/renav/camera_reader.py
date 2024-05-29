"""Module for reading cameras from Renav files."""

from pathlib import Path
from typing import Callable

import polars as pl

from result import Ok, Err, Result


RENAV_SKIP_ROWS: int = 58
RENAV_SEPARATOR: str = "\t"
RENAV_DATAFRAME_COLUMNS: list = [
    "identifier",
    "timestamp",
    "latitude",
    "longitude",
    "position_x",
    "position_y",
    "position_z",
    "euler_x",
    "euler_y",
    "euler_z",
    "left_image_name",
    "right_image_name",
    "altitude",
    "bounding_radius",
    "likely_crossover",
]


def preprocess_and_cast_columns(cameras: pl.DataFrame) -> pl.DataFrame:
    """Preprocesses column string values and casts them to the polars data types."""

    cameras: pl.DataFrame = cameras.with_columns(
        [
            pl.col("identifier").str.strip_chars().cast(pl.Int64),
            pl.col("timestamp").str.strip_chars().cast(pl.Float64),
            pl.col("latitude").str.strip_chars().cast(pl.Float64),
            pl.col("longitude").str.strip_chars().cast(pl.Float64),
            pl.col("position_x").str.strip_chars().cast(pl.Float32),
            pl.col("position_y").str.strip_chars().cast(pl.Float32),
            pl.col("position_z").str.strip_chars().cast(pl.Float32),
            pl.col("euler_x").str.strip_chars().cast(pl.Float32),
            pl.col("euler_y").str.strip_chars().cast(pl.Float32),
            pl.col("euler_z").str.strip_chars().cast(pl.Float32),
            pl.col("left_image_name").str.strip_chars(),
            pl.col("right_image_name").str.strip_chars(),
            pl.col("altitude").str.strip_chars().cast(pl.Float32),
            pl.col("bounding_radius").str.strip_chars().cast(pl.Float32),
            pl.col("likely_crossover") == "1",
        ]
    )
    return cameras


def read_cameras(
    path: Path, preprocessor: Callable[[pl.DataFrame], pl.DataFrame] = None
) -> Result[pl.DataFrame, str]:
    """Reads cameras from a Renav file."""

    if not path.exists():
        return Err(f"file does not exist: {path}")

    try:
        cameras: pl.DataFrame = pl.read_csv(
            source=path,
            new_columns=RENAV_DATAFRAME_COLUMNS,
            has_header=False,
            separator=RENAV_SEPARATOR,
            skip_rows=RENAV_SKIP_ROWS,
            infer_schema_length=0, # NOTE: Makes sure all columns are interpreted as strings
        )
    except pl.exceptions.ComputeError as error:
        return Err(error)

    cameras: pl.DataFrame = preprocess_and_cast_columns(cameras)

    if preprocessor:
        cameras: pl.DataFrame = preprocessor(cameras)

    return Ok(cameras)
