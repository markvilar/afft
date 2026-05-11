"""Runner for the table ingestion task."""

import afft.env  # noqa: F401
import os
from pathlib import Path

import pandas as pd
import sqlalchemy as sqla
from tqdm import tqdm

from afft.utils.log import logger

from .types import IngestTableResult, IngestTablesCommand


def run_ingest_tables(command: IngestTablesCommand) -> None:
    """Read CSV files from a directory and ingest each as a database table."""
    assert "DATABASE_URL" in os.environ, (
        "missing environment variable: DATABASE_URL"
    )

    engine: sqla.Engine = sqla.create_engine(os.environ["DATABASE_URL"])

    files: list[Path] = sorted(command.source_dir.glob(command.pattern))

    if not files:
        raise FileNotFoundError(
            f"no files matching '{command.pattern}' in {command.source_dir}"
        )

    if_exists: str = "replace" if command.overwrite else "fail"

    results: list[IngestTableResult] = []

    progress: tqdm = tqdm(files, unit="table")
    for file in progress:
        progress.set_description(file.stem)
        df: pd.DataFrame = pd.read_csv(file)
        df.to_sql(file.stem, con=engine, if_exists=if_exists, index=False)
        results.append(
            IngestTableResult(file=file, table=file.stem, rows=len(df))
        )

    if command.verbose:
        logger.info("Ingestion summary:")
        for result in results:
            logger.info(
                f"  {result.file.name} -> {result.table}: {result.rows} rows"
            )
