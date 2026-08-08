"""Sensor-agnostic column processors, written directly against
`PipelineProcessor`."""

from collections.abc import Mapping

import pandas as pd

from pydantic import BaseModel, ConfigDict

from .registry import register_processor


class RenameColumnsConfig(BaseModel):
    """
    Configuration for `rename_columns`.

    Attributes
    ----------
    columns: Maps each existing column name to its new name.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    columns: dict[str, str]


class SelectColumnsConfig(BaseModel):
    """
    Configuration for `select_columns`.

    Attributes
    ----------
    columns: Column names to keep, in the order they should appear.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    columns: list[str]


class DropColumnsConfig(BaseModel):
    """
    Configuration for `drop_columns`.

    Attributes
    ----------
    columns: Column names to remove.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    columns: list[str]


@register_processor("rename_columns", config_type=RenameColumnsConfig)
def rename_columns(
    frames: Mapping[str, pd.DataFrame],
    config: RenameColumnsConfig,
) -> pd.DataFrame:
    """
    Rename columns on a single frame.

    Arguments
    ---------
    frames: Single-entry mapping holding the frame under `df`.
    config: Holds the old-name-to-new-name mapping.

    Returns
    -------
    The frame with its columns renamed.

    Raises
    ------
    KeyError: If a column named for renaming is not in the frame.
    """
    frame = frames["df"]
    missing = [name for name in config.columns if name not in frame.columns]
    if missing:
        raise KeyError(f"columns not in frame: {missing}")
    return frame.rename(columns=dict(config.columns))


@register_processor("select_columns", config_type=SelectColumnsConfig)
def select_columns(
    frames: Mapping[str, pd.DataFrame],
    config: SelectColumnsConfig,
) -> pd.DataFrame:
    """
    Keep only the listed columns of a single frame.

    Arguments
    ---------
    frames: Single-entry mapping holding the frame under `df`.
    config: Holds the column names to keep.

    Returns
    -------
    The frame reduced to the listed columns, in the listed order.

    Raises
    ------
    KeyError: If a column named for keeping is not in the frame.
    """
    frame = frames["df"]
    missing = [name for name in config.columns if name not in frame.columns]
    if missing:
        raise KeyError(f"columns not in frame: {missing}")
    return frame[config.columns]


@register_processor("drop_columns", config_type=DropColumnsConfig)
def drop_columns(
    frames: Mapping[str, pd.DataFrame],
    config: DropColumnsConfig,
) -> pd.DataFrame:
    """
    Remove the listed columns from a single frame.

    Arguments
    ---------
    frames: Single-entry mapping holding the frame under `df`.
    config: Holds the column names to remove.

    Returns
    -------
    The frame without the listed columns.

    Raises
    ------
    KeyError: If a column named for removal is not in the frame.
    """
    frame = frames["df"]
    missing = [name for name in config.columns if name not in frame.columns]
    if missing:
        raise KeyError(f"columns not in frame: {missing}")
    return frame.drop(columns=config.columns)
