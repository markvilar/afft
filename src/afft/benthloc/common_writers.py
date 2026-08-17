"""Writers shared by both Benthloc ingestion file builders."""

from pathlib import Path

import geopandas as gpd


def write_feature_collection_file(
    frame: gpd.GeoDataFrame,
    output_file: Path,
    *,
    overwrite: bool = False,
) -> None:
    """
    Write a geoframe to a GeoJSON `FeatureCollection` file, one row per
    `Feature`.

    Arguments
    ---------
    frame: Geoframe to write.
    output_file: Path to write to.
    overwrite: Overwrite `output_file` if it already exists.

    Raises
    ------
    FileExistsError: If `output_file` already exists and `overwrite` is not
        set.
    """
    if output_file.exists() and not overwrite:
        raise FileExistsError(f"output file already exists: {output_file}")
    frame.to_file(output_file, driver="GeoJSON")
