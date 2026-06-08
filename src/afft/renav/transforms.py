"""Domain transforms for Renav camera pose DataFrames."""

import math

from pathlib import Path

import pandas as pd


def convert_camera_attitude_to_degrees(cameras: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Euler angles in a camera pose DataFrame from radians to degrees.

    Arguments
    ---------
    cameras: DataFrame containing ``euler_x``, ``euler_y``, ``euler_z`` columns
        in radians.

    Returns
    -------
    DataFrame with the same columns converted to degrees.
    """
    cameras = cameras.copy()
    cameras["euler_x"] = cameras["euler_x"] * 180.0 / math.pi
    cameras["euler_y"] = cameras["euler_y"] * 180.0 / math.pi
    cameras["euler_z"] = cameras["euler_z"] * 180.0 / math.pi
    return cameras


def transform_camera_attitude_to_vehicle(cameras: pd.DataFrame) -> pd.DataFrame:
    """
    Derive vehicle roll, pitch, and heading from camera Euler angles.

    Assumes Euler angles are already in degrees. The heading is the
    camera z-rotation shifted by -90°, clamped to [0, 360]. Roll flips
    the x-axis sign to convert from image-down to vehicle-forward convention.

    Arguments
    ---------
    cameras: DataFrame with ``euler_x``, ``euler_y``, ``euler_z`` columns
        in degrees.

    Returns
    -------
    DataFrame with added ``roll``, ``pitch``, and ``heading`` columns.
    """
    cameras = cameras.copy()
    cameras["heading"] = cameras["euler_z"] - 90.0
    cameras["heading"] = cameras["heading"].where(
        cameras["heading"] >= 0.0, cameras["heading"] + 360.0
    )
    cameras["roll"] = cameras["euler_x"] * -1.0
    cameras["pitch"] = cameras["euler_y"].copy()
    return cameras


def add_image_labels(cameras: pd.DataFrame) -> pd.DataFrame:
    """
    Add image label columns derived from the stereo image filename stems.

    Arguments
    ---------
    cameras: DataFrame with ``stereo_left_image_name`` and
        ``stereo_right_image_name`` columns.

    Returns
    -------
    DataFrame with added ``stereo_left_label`` and ``stereo_right_label``
    columns.
    """
    cameras = cameras.copy()
    cameras["stereo_left_label"] = cameras["stereo_left_image_name"].map(
        lambda name: Path(name).stem
    )
    cameras["stereo_right_label"] = cameras["stereo_right_image_name"].map(
        lambda name: Path(name).stem
    )
    return cameras
