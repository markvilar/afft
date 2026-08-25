"""Tests for the sensor-agnostic column processors."""

import geopandas as gpd
import pandas as pd
import pytest

from pydantic import BaseModel

from afft.bundle_processing import (
    DropColumnsConfig,
    PipelineProcessor,
    RenameColumnsConfig,
    SelectColumnsConfig,
)
from afft.bundle_processing.common_processors import (
    drop_columns,
    rename_columns,
    select_columns,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {"timestamp": [1.0, 2.0], "depth": [3.0, 4.0], "extra": [5.0, 6.0]}
    )


def test_rename_columns_renames_the_listed_columns() -> None:
    """Listed columns are renamed and the rest are left alone."""
    config = RenameColumnsConfig(columns={"depth": "depth_m"})

    result = rename_columns({"df": _frame()}, config)

    assert list(result.columns) == ["timestamp", "depth_m", "extra"]


def test_rename_columns_preserves_geoframe_type_and_crs() -> None:
    """A geoframe input comes back out as a geoframe, with its CRS intact."""
    geoframe = gpd.GeoDataFrame(
        {"heading": [1.0, 2.0]},
        geometry=gpd.points_from_xy([1.0, 2.0], [3.0, 4.0]),
        crs="EPSG:4326",
    )
    config = RenameColumnsConfig(columns={"heading": "yaw"})

    result = rename_columns({"df": geoframe}, config)

    assert isinstance(result, gpd.GeoDataFrame)
    assert list(result.columns) == ["yaw", "geometry"]
    assert result.crs == geoframe.crs


def test_select_columns_keeps_the_listed_order() -> None:
    """The result holds exactly the listed columns, in the listed order."""
    config = SelectColumnsConfig(columns=["depth", "timestamp"])

    result = select_columns({"df": _frame()}, config)

    assert list(result.columns) == ["depth", "timestamp"]


def test_drop_columns_removes_the_listed_columns() -> None:
    """Listed columns are removed and the rest survive."""
    config = DropColumnsConfig(columns=["extra"])

    result = drop_columns({"df": _frame()}, config)

    assert list(result.columns) == ["timestamp", "depth"]


@pytest.mark.parametrize(
    ("processor", "config"),
    [
        (rename_columns, RenameColumnsConfig(columns={"absent": "renamed"})),
        (select_columns, SelectColumnsConfig(columns=["absent"])),
        (drop_columns, DropColumnsConfig(columns=["absent"])),
    ],
)
def test_naming_an_absent_column_raises(
    processor: PipelineProcessor, config: BaseModel
) -> None:
    """A column that is not in the frame is an error, not a silent no-op."""
    with pytest.raises(KeyError, match="absent"):
        processor({"df": _frame()}, config)


def test_processors_do_not_mutate_their_input() -> None:
    """A processor returns a new frame rather than editing the one it read."""
    frame = _frame()

    drop_columns({"df": frame}, DropColumnsConfig(columns=["extra"]))

    assert "extra" in frame.columns
