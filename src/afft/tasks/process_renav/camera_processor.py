"""Task-level cleaning of Renav camera pose DataFrames."""

import polars as pl

from afft.renav.transforms import (
    add_image_labels,
    convert_camera_attitude_to_degrees,
    transform_camera_attitude_to_vehicle,
)


def clean_camera_dataframe(cameras: pl.DataFrame) -> pl.DataFrame:
    """
    Clean a raw Renav camera pose DataFrame for downstream use.

    Renames image columns, derives height/depth from z-position, adds image
    labels, converts and transforms attitude, drops intermediate columns, and
    reorders to a canonical column layout.

    Arguments
    ---------
    cameras: Raw DataFrame as returned by ``read_cameras``.

    Returns
    -------
    Cleaned DataFrame with a fixed column schema.
    """
    cameras = cameras.rename(
        {
            "left_image_name": "stereo_left_image_name",
            "right_image_name": "stereo_right_image_name",
        }
    )
    cameras = cameras.with_columns(
        [
            -pl.col("position_z").alias("height"),
            pl.col("position_z").alias("depth"),
        ]
    )
    cameras = add_image_labels(cameras)
    cameras = convert_camera_attitude_to_degrees(cameras)
    cameras = transform_camera_attitude_to_vehicle(cameras)
    cameras = cameras.drop(
        [
            "identifier",
            "likely_crossover",
            "position_x",
            "position_y",
            "position_z",
            "euler_x",
            "euler_y",
            "euler_z",
        ]
    )
    cameras = cameras.select(
        [
            pl.col("stereo_left_label"),
            pl.col("stereo_right_label"),
            pl.col("timestamp"),
            pl.col("latitude"),
            pl.col("longitude"),
            pl.col("height"),
            pl.col("depth"),
            pl.col("roll"),
            pl.col("pitch"),
            pl.col("heading"),
            pl.col("altitude"),
            pl.col("bounding_radius"),
            pl.col("stereo_left_image_name"),
            pl.col("stereo_right_image_name"),
        ]
    )
    return cameras
