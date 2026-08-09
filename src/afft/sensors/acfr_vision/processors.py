"""Stereo camera pair processor for ACFR vision systems."""

import pandas as pd

from .types import StereoPairingConfig, StereoPairingResult


def pair_stereo_images(
    df: pd.DataFrame,
    config: StereoPairingConfig = StereoPairingConfig(),
) -> StereoPairingResult:
    """Pair left and right stereo image captures into single rows per trigger.

    Steps:
    1. Deduplicate rows by label (same image logged multiple times).
    2. Split into left (left_suffix) and right (right_suffix) groups.
    3. Nearest trigger-time join: each left image is matched to the closest
       right image within max_offset_ms.
    4. Drop unmatched images on both sides.

    The trigger column must be datetime64; the caller is responsible for
    decoding whatever the source stores into datetime before calling.

    The discard counts are returned rather than logged, leaving it to the
    caller to decide how they are reported.

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
    )

    right = right.rename(
        columns={
            config.label_col: "right_label",
            config.filename_col: "right_filename",
            config.timestamp_col: "right_received_at",
            config.trigger_col: "right_timestamp",
            "exposure_logged": "right_exposure_logged",
            "exposure": "right_exposure",
        }
    )

    # Match on trigger time — both cameras receive the same trigger signal.
    result_frame: pd.DataFrame = pd.merge_asof(
        left.sort_values("left_timestamp"),
        right.sort_values("right_timestamp"),
        left_on="left_timestamp",
        right_on="right_timestamp",
        tolerance=pd.Timedelta(milliseconds=config.max_offset_ms),
        direction="nearest",
    )

    n_left_unmatched: int = int(result_frame["right_label"].isna().sum())
    if n_left_unmatched:
        result_frame = result_frame.dropna(subset=["right_label"]).reset_index(
            drop=True
        )

    if result_frame.empty:
        raise ValueError("no stereo pairs remain after timestamp matching")

    # Unmatched left rows widen the right columns to hold the fill NaN — bool
    # to object, int to float. Dropping those rows does not narrow them back,
    # so restore the dtypes the right frame came in with.
    result_frame = result_frame.astype(
        {
            column: right[column].dtype
            for column in right
            if column in result_frame.columns
        }
    )

    # Keep the closest left image for each right image.
    delta: pd.Series = (
        result_frame["left_timestamp"] - result_frame["right_timestamp"]
    ).abs()
    result_frame = (
        result_frame.assign(_delta=delta)
        .sort_values("_delta")
        .drop_duplicates(subset=["right_label"], keep="first")
        .drop(columns=["_delta"])
        .sort_values("left_timestamp")
        .reset_index(drop=True)
    )

    # The merge is a left join, so right images that matched nothing never
    # entered the frame. Account for them against the input right images.
    n_right_unmatched: int = len(right) - int(
        result_frame["right_label"].nunique()
    )

    result_frame["timestamp"] = result_frame["left_timestamp"]

    result_frame = result_frame[
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

    return StereoPairingResult(
        frame=result_frame,
        left_total=len(left),
        right_total=len(right),
        left_unmatched=n_left_unmatched,
        right_unmatched=n_right_unmatched,
    )
