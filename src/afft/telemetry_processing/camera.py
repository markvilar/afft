"""Stereo camera pair processor."""

from dataclasses import dataclass

import pandas as pd

from .pipeline import register_processor


@dataclass(slots=True, frozen=True)
class PairStereoImagesConfig:
    left_suffix: str = "LC16"
    right_suffix: str = "RM16"
    label_col: str = "label"
    filename_col: str = "filename"
    trigger_col: str = "trigger_time"
    timestamp_col: str = "timestamp"
    max_offset_ms: float = 30.0


@register_processor("pair_stereo_images")
def pair_stereo_images(
    df: pd.DataFrame,
    config: PairStereoImagesConfig = PairStereoImagesConfig(),
) -> pd.DataFrame:
    """Pair left and right stereo image captures into single rows per trigger.

    Steps:
    1. Deduplicate rows by label (same image logged multiple times).
    2. Split into left (left_suffix) and right (right_suffix) groups.
    3. Inner-join on trigger_time.
    4. Validate that message timestamps are within max_offset_ms.
    """
    df = df.drop_duplicates(
        subset=[config.label_col], keep="first"
    ).reset_index(drop=True)

    left_mask: pd.Series = df[config.filename_col].str.contains(
        config.left_suffix, regex=False
    )
    right_mask: pd.Series = df[config.filename_col].str.contains(
        config.right_suffix, regex=False
    )

    left: pd.DataFrame = df[left_mask].copy()
    right: pd.DataFrame = df[right_mask].copy()

    if left.empty:
        raise ValueError(f"no rows matching left_suffix={config.left_suffix!r}")
    if right.empty:
        raise ValueError(
            f"no rows matching right_suffix={config.right_suffix!r}"
        )

    left = left.rename(
        columns={
            config.label_col: "left_label",
            config.filename_col: "left_filename",
            config.timestamp_col: "left_timestamp",
        }
    ).drop(columns=["topic"], errors="ignore")

    right = right.rename(
        columns={
            config.label_col: "right_label",
            config.filename_col: "right_filename",
            config.timestamp_col: "right_timestamp",
        }
    ).drop(columns=["topic", "exposure_logged", "exposure"], errors="ignore")

    paired: pd.DataFrame = pd.merge(
        left, right, on=config.trigger_col, how="inner"
    )

    if paired.empty:
        raise ValueError(
            f"no stereo pairs found — "
            f"left: {len(left)} rows, right: {len(right)} rows"
        )

    left_ts: pd.Series = pd.to_datetime(paired["left_timestamp"])
    right_ts: pd.Series = pd.to_datetime(paired["right_timestamp"])
    delta_ms: pd.Series = (left_ts - right_ts).abs().dt.total_seconds() * 1000.0

    exceeds: pd.Series = delta_ms > config.max_offset_ms
    if exceeds.any():
        n: int = int(exceeds.sum())
        worst: float = float(delta_ms.max())
        raise ValueError(
            f"{n} stereo pair(s) exceed {config.max_offset_ms} ms timestamp "
            f"offset (worst: {worst:.1f} ms)"
        )

    return paired[
        [
            config.trigger_col,
            "left_label",
            "right_label",
            "left_filename",
            "right_filename",
            "left_timestamp",
            "right_timestamp",
            "exposure_logged",
            "exposure",
        ]
    ].reset_index(drop=True)
