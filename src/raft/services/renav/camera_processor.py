"""Module for processing dataframes with camera data from Renav."""

import math

from pathlib import Path

import polars as pl

from result import Ok, Err, Result


def convert_camera_attitude_to_degrees(cameras: pl.DataFrame) -> pl.DataFrame:
    """Converts the Euler angles representing the camera attitude from radians
    to degrees."""
    # Convert attitude to degrees
    cameras: pl.DataFrame = cameras.with_columns(
        [
            cameras["euler_x"] * 180.0 / math.pi,
            cameras["euler_y"] * 180.0 / math.pi,
            cameras["euler_z"] * 180.0 / math.pi,
        ]
    )
    return cameras


def transform_camera_attitude_to_vehicle(cameras: pl.DataFrame) -> pl.DataFrame:
    """Adds vehicle attitude columns, i.e. roll, pitch, and heading, from the
    Euler angles representing the attitude of the stereo camera.
    Assumes the camera attitude is given in degrees."""

    # Shift z-rotation to get vehicle heading
    cameras: pl.DataFrame = cameras.with_columns(
        [
            (pl.col("euler_z") - 90.0).alias("heading"),
        ]
    )

    # Clamp updated z-rotation in the interval [0, 360]
    cameras = cameras.with_columns(
        pl.when(pl.col("heading") < 0.0)
        .then(pl.col("heading") + 360)
        .otherwise(pl.col("heading"))
        .alias("heading")
    )

    # Correct roll - flip axis from image down to vehicle forward
    cameras = cameras.with_columns((pl.col("euler_x") * -1.0).alias("roll"))

    # Correct pitch
    cameras = cameras.with_columns((pl.col("euler_y")).alias("pitch"))
    return cameras


def add_image_labels(cameras: pl.DataFrame) -> pl.DataFrame:
    """Add image labels as the stem of the corresponding image files."""

    stereo_left_image_names: list[str] = cameras["stereo_left_image_name"].to_list()
    stereo_right_image_names: list[str] = cameras["stereo_right_image_name"].to_list()

    stereo_left_labels: list[str] = [
        Path(name).stem for name in stereo_left_image_names
    ]
    stereo_right_labels: list[str] = [
        Path(name).stem for name in stereo_right_image_names
    ]

    cameras: pl.DataFrame = cameras.with_columns(
        [
            pl.Series(name="stereo_left_label", values=stereo_left_labels),
            pl.Series(name="stereo_right_label", values=stereo_right_labels),
        ]
    )

    return cameras


def clean_camera_dataframe(cameras: pl.DataFrame) -> pl.DataFrame:
    """Cleans a dataframe of cameras from a Renav file by processing image files and labels,
    and compute vehicle attitudes, height, and depth. Additionally, unnecessary columns are
    dropped from the dataframe."""

    # Rename image filename columns to highlight that they are capture by a stereo camera
    cameras: pl.DataFrame = cameras.rename(
        {
            "left_image_name": "stereo_left_image_name",
            "right_image_name": "stereo_right_image_name",
        }
    )

    # Add negative and positive z-position as height and depth, respectively
    cameras: pl.DataFrame = cameras.with_columns(
        [
            -pl.col("position_z").alias("height"),
            pl.col("position_z").alias("depth"),
        ]
    )

    # Create image labels and file names
    cameras: pl.DataFrame = add_image_labels(cameras)

    # Convert and transform camera / vehicle attitudes
    cameras: pl.DataFrame = convert_camera_attitude_to_degrees(cameras)
    cameras: pl.DataFrame = transform_camera_attitude_to_vehicle(cameras)

    # Drop unnecessary columns
    cameras: pl.DataFrame = cameras.drop(
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

    # Reorder columns in dataframe
    cameras: pl.DataFrame = cameras.select(
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
