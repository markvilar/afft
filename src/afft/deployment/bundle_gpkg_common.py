"""Helpers shared by the GeoPackage deployment bundle reader, writer, and
read-write implementations."""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio


def layer_exists(path: Path, layer: str) -> bool:
    """Return whether `path` has a layer called `layer`."""
    if not path.exists():
        return False
    return layer in gpd.list_layers(path)["name"].values


def read_contents(path: Path) -> pd.DataFrame:
    """Read `path`'s layer manifest, or an empty frame of the right shape if
    the bundle has no layers yet.

    `gpd.list_layers` raises for a nonexistent file rather than returning an
    empty result, so a bundle that has not been written to yet is handled
    explicitly here. `geometry_type` is `None` for a non-spatial layer, and
    the geometry type name (`"Point"`, `"LineString"`, etc.) for a spatial
    one -- this is what `is_geoframe` checks against.
    """
    if not path.exists():
        return pd.DataFrame(columns=["identifier", "geometry_type"])
    return gpd.list_layers(path).rename(columns={"name": "identifier"})


def write_frame_table(
    path: Path, layer: str, frame: pd.DataFrame | gpd.GeoDataFrame
) -> None:
    """
    Write `frame` to `path` as the layer `layer`, replacing any existing
    layer of that name.

    `pyogrio.write_dataframe` accepts both a plain `DataFrame` and a
    `GeoDataFrame` uniformly, writing a non-spatial layer for the former and
    a spatial one for the latter -- unlike `DataFrame.to_file`, which only
    plain `DataFrame` lacks.
    """
    pyogrio.write_dataframe(frame, path, layer=layer)


def read_frame_table(path: Path, layer: str) -> pd.DataFrame | gpd.GeoDataFrame:
    """Read the layer `layer` from `path`, as a `GeoDataFrame` if it is
    spatial or a plain `DataFrame` otherwise."""
    return gpd.read_file(path, layer=layer)


def list_frames(contents: pd.DataFrame) -> list[str]:
    """List the identifiers of `contents`' plain (non-spatial) rows."""
    return list(contents.loc[contents["geometry_type"].isna(), "identifier"])


def list_geoframes(contents: pd.DataFrame) -> list[str]:
    """List the identifiers of `contents`' geospatial rows."""
    return list(contents.loc[contents["geometry_type"].notna(), "identifier"])


def geometry_type(contents: pd.DataFrame, key: str) -> str | None:
    """
    Look up `key`'s `geometry_type` in a `read_contents` frame.

    Raises
    ------
    KeyError: If `key` is not in `contents`.
    """
    matches = contents.loc[contents["identifier"] == key, "geometry_type"]
    if matches.empty:
        raise KeyError(key)
    value = matches.iloc[0]
    return None if value is None else str(value)


def validate_geoframe(frame: gpd.GeoDataFrame) -> None:
    """
    Validate that `frame` is writable through `write_geoframe`.

    Raises
    ------
    TypeError: If `frame` is not a `GeoDataFrame`, or has no active
        geometry column set.
    ValueError: If `frame`'s geometry is entirely empty/null, or its CRS
        is not set.
    """
    if not isinstance(frame, gpd.GeoDataFrame):
        raise TypeError(f"frame is not a GeoDataFrame: {type(frame)}")
    try:
        geometry = frame.geometry
    except AttributeError as error:
        raise TypeError("frame has no active geometry column set") from error
    if geometry.is_empty.all() or geometry.isna().all():
        raise ValueError("frame's geometry is entirely empty or null")
    if frame.crs is None:
        raise ValueError("frame's CRS is not set")
