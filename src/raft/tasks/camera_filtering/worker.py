"""Module for a worker for filtering cameras from Renav files."""

from pathlib import Path

import polars as pl

from result import Ok, Err, Result

from raft.io import read_file
from raft.services.renav import read_cameras, clean_camera_dataframe
from raft.utils.log import logger

from .data_types import CameraFilteringContext, CameraFilteringData


def prepare_camera_processing_data(
    context: CameraFilteringContext,
) -> CameraFilteringData:
    """Reads cameras and labels from file. Additionally, cameras are cleaned by renaming and dropping
    unnecessary columns."""

    camera_read_result: Result[pl.DataFrame, str] = read_cameras(context.camera_file)
    if camera_read_result.is_err():
        logger.error(camera_read_result.err())

    # Read camera
    cameras: pl.DataFrame = camera_read_result.ok()
    cameras: pl.DataFrame = clean_camera_dataframe(cameras)

    if context.has_labels:
        label_read_result: Result[pl.DataFrame, str] = read_file(context.label_file)
        labels: list[str] = label_read_result.unwrap()
    else:
        labels = None

    return CameraFilteringData(cameras, labels)


def filter_cameras_by_label(cameras: pl.DataFrame, labels: list[str]) -> pl.DataFrame:
    """Filter a camera data frame by the given labels. Cameras whose label is not in the given label
    are discarded."""

    filtered_cameras: pl.DataFrame = cameras.filter(
        pl.col("stereo_left_label").is_in(labels)
    )

    logger.info(
        f"Filter by label - Kept {len(filtered_cameras)} out of {len(cameras)} cameras"
    )

    return filtered_cameras


def write_cameras_to_csv(cameras: pl.DataFrame, path: Path) -> Result[Path, str]:
    """Writes a camera data frame to a CSV file."""
    if not path.suffix == ".csv":
        return Err(f"invalid file extension: {path}")

    error: Optional[str] = cameras.write_csv(path)

    if error:
        return Err(error)
    else:
        return Ok(path)


def filter_cameras(context: CameraFilteringContext) -> None:
    """Worker function for filtering Renav cameras."""

    if context.camera_file == context.output_file:
        logger.error("camera and output file cannot be the same")
        return

    task_data: CameraFilteringData = prepare_camera_processing_data(context)

    if task_data.has_labels:
        filtered_cameras: pl.DataFrame = filter_cameras_by_label(
            task_data.cameras, task_data.labels
        )
    else:
        filtered_cameras: pl.DataFrame = task_data.cameras

    # Save cameras to file
    write_result: Result[Path, str] = write_cameras_to_csv(
        filtered_cameras, context.output_file
    )

    if write_result.is_err():
        logger.error(write_result.err())
    else:
        logger.info(f"wrote cameras to file: {write_result.ok()}")
