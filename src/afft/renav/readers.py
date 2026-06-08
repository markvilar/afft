"""Readers for Renav navigation files."""

from pathlib import Path
from typing import Callable, Optional

import pandas as pd


RENAV_SKIP_ROWS: int = 58
RENAV_SEPARATOR: str = "\t"
RENAV_COLUMNS: list[str] = [
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

_COLUMN_DTYPES: dict[str, str] = {
    "identifier": "int64",
    "timestamp": "float64",
    "latitude": "float64",
    "longitude": "float64",
    "position_x": "float32",
    "position_y": "float32",
    "position_z": "float32",
    "euler_x": "float32",
    "euler_y": "float32",
    "euler_z": "float32",
    "altitude": "float32",
    "bounding_radius": "float32",
}


def _preprocess_and_cast_columns(cameras: pd.DataFrame) -> pd.DataFrame:
    string_columns: list[str] = ["left_image_name", "right_image_name"]
    for column in string_columns:
        cameras[column] = cameras[column].str.strip()

    cameras["likely_crossover"] = cameras["likely_crossover"].str.strip() == "1"

    for column, dtype in _COLUMN_DTYPES.items():
        cameras[column] = cameras[column].str.strip().astype(dtype)

    return cameras


def read_cameras(
    path: Path,
    preprocessor: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
) -> pd.DataFrame:
    """
    Read camera pose estimates from a Renav file.

    Arguments
    ---------
    path: Path to the Renav `.data` file.
    preprocessor: Optional transform applied after column casting.

    Returns
    -------
    DataFrame with one row per camera pose estimate.
    """
    if not path.exists():
        raise FileNotFoundError(f"file does not exist: {path}")

    cameras: pd.DataFrame = pd.read_csv(
        path,
        names=RENAV_COLUMNS,
        header=None,
        sep=RENAV_SEPARATOR,
        skiprows=RENAV_SKIP_ROWS,
        dtype=str,
    )

    cameras = _preprocess_and_cast_columns(cameras)

    if preprocessor is not None:
        cameras = preprocessor(cameras)

    return cameras
