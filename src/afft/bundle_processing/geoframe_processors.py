"""Generic geometry construction from named coordinate columns, as distinct
from `pose_processors`, which holds pose-specific geometric transforms."""

from collections.abc import Mapping

import geopandas as gpd
import pandas as pd

from pydantic import BaseModel, ConfigDict

from .processor_registry import register_processor


class BuildGeoframeFromFrameConfig(BaseModel):
    """
    Column configuration for the build geoframe from frame pipeline step.

    Attributes
    ----------
    x_column: Column holding the geometry's X coordinate (e.g. longitude, easting).
    y_column: Column holding the geometry's Y coordinate (e.g. latitude, northing).
    z_column: Optional column holding the geometry's Z coordinate (e.g. height).
        Omit for 2D points.
    crs: EPSG code the x/y/z columns are expressed in. Required -- there is no
        default, so the caller always states what the coordinates mean.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    x_column: str
    y_column: str
    z_column: str | None = None
    crs: str


def build_geoframe_from_frame(
    frame: pd.DataFrame,
    config: BuildGeoframeFromFrameConfig,
) -> gpd.GeoDataFrame:
    """
    Construct a geoframe from named x/y(/z) columns in a plain frame.

    Rows with a NaN x, y, or (when configured) z coordinate are dropped
    before building geometry, rather than producing null-geometry rows.

    Arguments
    ---------
    frame: Source frame holding the coordinate columns.
    config: Column names and CRS to build the geometry from.

    Returns
    -------
    Geoframe with a `geometry` column built via `gpd.points_from_xy`, all
    other columns retained unchanged.
    """
    coordinate_columns: list[str] = [config.x_column, config.y_column]
    if config.z_column is not None:
        coordinate_columns.append(config.z_column)

    filtered: pd.DataFrame = frame.dropna(subset=coordinate_columns)

    z: pd.Series | None = (
        filtered[config.z_column] if config.z_column is not None else None
    )
    geometry = gpd.points_from_xy(
        filtered[config.x_column],
        filtered[config.y_column],
        z,
        crs=config.crs,
    )
    return gpd.GeoDataFrame(filtered, geometry=geometry, crs=config.crs)


@register_processor(
    "build_geoframe_from_frame", config_type=BuildGeoframeFromFrameConfig
)
def step_build_geoframe_from_frame(
    frames: Mapping[str, pd.DataFrame | gpd.GeoDataFrame],
    config: BuildGeoframeFromFrameConfig,
) -> gpd.GeoDataFrame:
    """Construct a geoframe from named x/y(/z) columns in a plain frame."""
    return build_geoframe_from_frame(frames["frame"], config)
