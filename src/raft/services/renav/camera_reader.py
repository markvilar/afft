"""Module for reading cameras from Renav files."""

from pathlib import Path

import polars as pl

from result import Ok, Err, Result

from raft.utils.log import logger


def read_cameras(path: Path) -> Result[pl.DataFrame, str]:
    """Reads cameras from a Renav file."""
    if not path.exists():
        return Err(f"file does not exist: {path}")

    columns: list = [
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

    try:
        cameras: pl.DataFrame = pl.read_csv(
            source=path,
            new_columns=columns,
            has_header=False,
            separator="\t",
            skip_rows=58,
        )
    except pl.exceptions.ComputeError as error:
        return Err(error)

    cameras: pl.DataFrame = cameras.with_columns(
        [
            cameras["identifier"].str.strip_chars().cast(pl.Int64),
            cameras["timestamp"].str.strip_chars().cast(pl.Float32),
            cameras["latitude"].str.strip_chars().cast(pl.Float32),
            cameras["longitude"].str.strip_chars().cast(pl.Float32),
            cameras["position_x"].str.strip_chars().cast(pl.Float32),
            cameras["position_y"].str.strip_chars().cast(pl.Float32),
            cameras["position_z"].str.strip_chars().cast(pl.Float32),
            cameras["euler_x"].str.strip_chars().cast(pl.Float32),
            cameras["euler_y"].str.strip_chars().cast(pl.Float32),
            cameras["euler_z"].str.strip_chars().cast(pl.Float32),
            cameras["left_image_name"].str.strip_chars(),
            cameras["right_image_name"].str.strip_chars(),
            cameras["altitude"].str.strip_chars().cast(pl.Float32),
            cameras["bounding_radius"].str.strip_chars().cast(pl.Float32),
            cameras["likely_crossover"].cast(pl.Boolean),
        ]
    )

    # TODO: Update yaw angle

    return Ok(cameras)
