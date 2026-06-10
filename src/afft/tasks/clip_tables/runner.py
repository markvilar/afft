"""Runner for the table clipping task."""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

from afft.utils.log import logger

from .types import ClipTableResult, ClipTablesCommand


def run_clip_tables(command: ClipTablesCommand) -> None:
    """Read CSV files from source_dir, clip rows to [start, end], write to output_dir."""
    files: list[Path] = sorted(command.source_dir.glob(command.pattern))

    if command.start >= command.end:
        raise ValueError(
            f"start must be before end: {command.start} >= {command.end}"
        )

    if not files:
        raise FileNotFoundError(
            f"no files matching '{command.pattern}' in {command.source_dir}"
        )

    if not command.output_dir.is_dir():
        raise ValueError(
            f"output directory does not exist: {command.output_dir}"
        )

    results: list[ClipTableResult] = []

    progress: tqdm = tqdm(files, unit="table")
    for file in progress:
        progress.set_description(file.stem)
        df: pd.DataFrame = pd.read_csv(file)
        df[command.timestamp_column] = pd.to_datetime(
            df[command.timestamp_column],
            format=command.timestamp_format,
            utc=True,
        )
        rows_in = len(df)
        mask = (df[command.timestamp_column] >= command.start) & (
            df[command.timestamp_column] <= command.end
        )
        clipped: pd.DataFrame = df[mask]
        dest = command.output_dir / file.name
        clipped.to_csv(dest, index=False)
        results.append(
            ClipTableResult(
                file=file,
                table=file.stem,
                rows_in=rows_in,
                rows_out=len(clipped),
            )
        )

    if all(r.rows_out == 0 for r in results):
        logger.warning(
            f"no rows found in [{command.start}, {command.end}] "
            f"across all {len(results)} file(s) — check files or time interval"
        )

    logger.info("Clip summary:")
    for result in results:
        logger.info(
            f"  {result.file.name}: {result.rows_in} -> {result.rows_out} rows"
        )
