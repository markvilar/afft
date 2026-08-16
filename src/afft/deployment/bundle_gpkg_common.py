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
    explicitly here.
    """
    if not path.exists():
        return pd.DataFrame(columns=["identifier"])
    return gpd.list_layers(path)[["name"]].rename(
        columns={"name": "identifier"}
    )


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
