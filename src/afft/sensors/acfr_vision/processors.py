"""Stereo camera pair processor for ACFR vision systems."""

import pandas as pd

from afft.telemetry_processing.pipeline import register_processor
from afft.utils.log import logger

from .types import PairStereoImagesConfig


def _to_float_seconds(series: pd.Series) -> pd.Series:
    """Normalise a timestamp series to float seconds since epoch.

    Handles both float Unix-second columns and ISO datetime strings.
    """
    numeric: pd.Series = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all():
        return numeric
    return pd.to_datetime(series).astype("int64") / 1e9


@register_processor("pair_stereo_images")
def pair_stereo_images(
    df: pd.DataFrame,
    config: PairStereoImagesConfig = PairStereoImagesConfig(),
) -> pd.DataFrame:
    """Pair left and right stereo image captures into single rows per trigger.

    Steps:
    1. Deduplicate rows by label (same image logged multiple times).
    2. Split into left (left_suffix) and right (right_suffix) groups.
    3. Nearest trigger-time join: each left image is matched to the closest
       right image within max_offset_ms.
    4. Drop unmatched rows; warn if > 20% are unmatched.

    Output timestamps:
      timestamp / left_timestamp / right_timestamp  — trigger time (capture time)
      left_received_at / right_received_at          — message logging time
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
            config.timestamp_col: "left_received_at",
            config.trigger_col: "left_timestamp",
            "exposure_logged": "left_exposure_logged",
            "exposure": "left_exposure",
        }
    ).drop(columns=["topic"], errors="ignore")

    right = right.rename(
        columns={
            config.label_col: "right_label",
            config.filename_col: "right_filename",
            config.timestamp_col: "right_received_at",
            config.trigger_col: "right_timestamp",
            "exposure_logged": "right_exposure_logged",
            "exposure": "right_exposure",
        }
    ).drop(columns=["topic"], errors="ignore")

    # Match on trigger time — both cameras receive the same trigger signal.
    tolerance_s: float = config.max_offset_ms / 1000.0
    left["_ts"] = _to_float_seconds(left["left_timestamp"])
    right["_ts"] = _to_float_seconds(right["right_timestamp"])

    paired: pd.DataFrame = pd.merge_asof(
        left.sort_values("_ts"),
        right.sort_values("_ts"),
        on="_ts",
        tolerance=tolerance_s,
        direction="nearest",
    ).drop(columns=["_ts"])

    n_unmatched: int = int(paired["right_label"].isna().sum())
    if n_unmatched:
        logger.info(
            f"dropped {n_unmatched} left image(s) with no right match "
            f"within {config.max_offset_ms} ms"
        )
        if n_unmatched / len(paired) > 0.20:
            logger.warning(
                f"{n_unmatched}/{len(paired)} left images "
                f"({100 * n_unmatched / len(paired):.1f}%) "
                f"had no matching right image within {config.max_offset_ms} ms"
            )
        paired = paired.dropna(subset=["right_label"]).reset_index(drop=True)

    if paired.empty:
        raise ValueError("no stereo pairs remain after timestamp matching")

    # Keep the closest left image for each right image.
    delta: pd.Series = (
        _to_float_seconds(paired["left_timestamp"])
        - _to_float_seconds(paired["right_timestamp"])
    ).abs()
    paired = (
        paired.assign(_delta=delta)
        .sort_values("_delta")
        .drop_duplicates(subset=["right_label"], keep="first")
        .drop(columns=["_delta"])
        .sort_values("left_timestamp")
        .reset_index(drop=True)
    )

    paired["timestamp"] = paired["left_timestamp"]

    return paired[
        [
            "timestamp",
            "left_label",
            "right_label",
            "left_filename",
            "right_filename",
            "left_timestamp",
            "right_timestamp",
            "left_received_at",
            "right_received_at",
            "left_exposure_logged",
            "left_exposure",
            "right_exposure_logged",
            "right_exposure",
        ]
    ].reset_index(drop=True)
