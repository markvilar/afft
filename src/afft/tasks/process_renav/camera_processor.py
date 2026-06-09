"""Task-level cleaning of Renav camera pose DataFrames."""

import pandas as pd

from afft.renav.transforms import (
    add_image_labels,
    convert_camera_attitude_to_degrees,
    swap_coordinates,
    transform_camera_attitude_to_vehicle,
)
from afft.renav.validators import (
    check_valid_positions_geodetic,
)

_OUTPUT_COLUMNS: list[str] = [
    "stereo_left_label",
    "stereo_right_label",
    "timestamp",
    "latitude",
    "longitude",
    "height",
    "depth",
    "roll",
    "pitch",
    "heading",
    "altitude",
    "bounding_radius",
    "stereo_left_image_name",
    "stereo_right_image_name",
]


def clean_camera_dataframe(cameras: pd.DataFrame) -> pd.DataFrame:
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
        columns={
            "left_image_name": "stereo_left_image_name",
            "right_image_name": "stereo_right_image_name",
        }
    )
    if not check_valid_positions_geodetic(cameras):
        cameras = swap_coordinates(cameras)
        if not check_valid_positions_geodetic(cameras):
            raise ValueError(
                f"invalid geodetic positions in {cameras.shape[0]} pose(s) "
                f"that cannot be corrected by swapping latitude and longitude"
            )
    cameras["timestamp"] = pd.to_datetime(
        cameras["timestamp"], unit="s", utc=True
    ).map(pd.Timestamp.isoformat)
    cameras["height"] = -cameras["position_z"]
    cameras["depth"] = cameras["position_z"].copy()
    cameras = add_image_labels(cameras)
    cameras = convert_camera_attitude_to_degrees(cameras)
    cameras = transform_camera_attitude_to_vehicle(cameras)
    cameras = cameras.drop(
        columns=[
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
    return cameras[_OUTPUT_COLUMNS].reset_index(drop=True)
