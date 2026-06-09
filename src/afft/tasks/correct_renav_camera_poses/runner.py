"""Runner for the correct renav camera poses task."""

from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

from afft.utils.log import logger

from .types import (
    CorrectRenavCameraPosesBatchCommand,
    CorrectRenavCameraPosesBatchResult,
    CorrectRenavCameraPosesCommand,
    CorrectRenavCameraPosesConfig,
    CorrectRenavCameraPosesResult,
)


def _correct_poses(
    target: pd.DataFrame,
    source: pd.DataFrame,
    config: CorrectRenavCameraPosesConfig,
) -> tuple[pd.DataFrame, CorrectRenavCameraPosesResult]:
    total: int = len(target)
    target = target.drop(
        columns=[config.target_latitude_column, config.target_longitude_column]
    )

    lookup: pd.DataFrame = source[
        [
            config.source_join_column,
            config.source_latitude_column,
            config.source_longitude_column,
        ]
    ].rename(
        columns={
            config.source_join_column: config.target_join_column,
            config.source_latitude_column: config.target_latitude_column,
            config.source_longitude_column: config.target_longitude_column,
        }
    )

    merged: pd.DataFrame = target.merge(
        lookup, on=config.target_join_column, how="left"
    )
    merged = merged.sort_values("timestamp").reset_index(drop=True)

    unmatched: int = int(merged[config.target_latitude_column].isna().sum())
    matched: int = total - unmatched

    merged[config.target_latitude_column] = merged[
        config.target_latitude_column
    ].interpolate(method="linear")
    merged[config.target_longitude_column] = merged[
        config.target_longitude_column
    ].interpolate(method="linear")

    remaining_nan: int = int(merged[config.target_latitude_column].isna().sum())
    interpolated: int = unmatched - remaining_nan

    result = CorrectRenavCameraPosesResult(
        total=total,
        matched=matched,
        unmatched=unmatched,
        interpolated=interpolated,
        remaining_nan=remaining_nan,
    )
    return merged, result


def run_correct_renav_camera_poses(
    command: CorrectRenavCameraPosesCommand,
    config: CorrectRenavCameraPosesConfig = CorrectRenavCameraPosesConfig(),
) -> CorrectRenavCameraPosesResult:
    """
    Correct Renav camera poses by overwriting latitude and longitude with
    values from a source camera pose file.

    Rows in the target frame that have no matching entry in the source frame
    receive NaN latitude and longitude before interpolation. Linear
    interpolation fills interior NaN values; leading and trailing NaNs remain.

    Arguments
    ---------
    command: Task configuration.
    config: Column label configuration.

    Returns
    -------
    Correction statistics for the deployment.
    """
    if not command.target_file.exists():
        raise FileNotFoundError(
            f"target file does not exist: {command.target_file}"
        )
    if not command.source_file.exists():
        raise FileNotFoundError(
            f"source file does not exist: {command.source_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )
    if command.output_file.resolve() == command.target_file.resolve():
        raise ValueError(
            f"output file must differ from target file: {command.target_file}"
        )

    target: pd.DataFrame = pd.read_csv(command.target_file)
    source: pd.DataFrame = pd.read_csv(command.source_file)

    corrected, result = _correct_poses(target, source, config)
    corrected.to_csv(command.output_file, index=False)

    logger.info(
        f"{command.target_file.name}: {result.matched} matched,"
        f" {result.unmatched} unmatched ({result.interpolated} interpolated,"
        f" {result.remaining_nan} remaining NaN) → {command.output_file}"
    )
    return result


def run_correct_renav_camera_poses_batch(
    command: CorrectRenavCameraPosesBatchCommand,
    config: CorrectRenavCameraPosesConfig = CorrectRenavCameraPosesConfig(),
) -> CorrectRenavCameraPosesBatchResult:
    """
    Batch-correct Renav camera poses by overwriting latitude and longitude
    with values from matching source camera pose files.

    For each target CSV in ``target_dir`` whose filename ends with
    ``target_suffix``, the deployment label is extracted and the corresponding
    source file (``{label}{source_suffix}``) is looked up in ``source_dir``.
    Target files with no matching source file are skipped with a warning.
    Per-deployment statistics are logged as a summary after all files are
    processed.

    Arguments
    ---------
    command: Task configuration.
    config: Column label configuration.

    Returns
    -------
    Per-deployment correction diagnostics and list of skipped labels.
    """
    if not command.target_dir.exists():
        raise FileNotFoundError(
            f"target directory does not exist: {command.target_dir}"
        )
    if not command.source_dir.exists():
        raise FileNotFoundError(
            f"source directory does not exist: {command.source_dir}"
        )
    if command.output_dir.resolve() == command.target_dir.resolve():
        raise ValueError(
            f"output directory must differ from target directory: "
            f"{command.target_dir}"
        )
    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )

    target_files: list[Path] = sorted(
        path
        for path in command.target_dir.iterdir()
        if path.is_file() and path.name.endswith(command.target_suffix)
    )
    if not target_files:
        raise FileNotFoundError(
            f"no target files ending in {command.target_suffix!r} "
            f"found in {command.target_dir}"
        )

    results: dict[str, CorrectRenavCameraPosesResult] = {}
    skipped: list[str] = []

    for target_file in tqdm(target_files, desc="Correcting poses", unit="file"):
        label: str = target_file.name.removesuffix(command.target_suffix)
        source_file: Path = (
            command.source_dir / f"{label}{command.source_suffix}"
        )

        if not source_file.exists():
            skipped.append(label)
            continue

        output_file: Path = command.output_dir / target_file.name

        target: pd.DataFrame = pd.read_csv(target_file)
        source: pd.DataFrame = pd.read_csv(source_file)

        corrected, result = _correct_poses(target, source, config)
        corrected.to_csv(output_file, index=False)
        results[label] = result

    diagnostics = CorrectRenavCameraPosesBatchResult(
        results=results, skipped=skipped
    )

    for label, result in diagnostics.results.items():
        logger.info(
            f"  {label}: {result.matched} matched,"
            f" {result.unmatched} unmatched ({result.interpolated} interpolated,"
            f" {result.remaining_nan} remaining NaN)"
        )
    for label in diagnostics.skipped:
        logger.warning(f"  {label}: no matching source file found, skipped")

    return diagnostics
