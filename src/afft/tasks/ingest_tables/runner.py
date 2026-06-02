"""Runner for the table ingestion task."""

from pathlib import Path

from afft.env import requireenv

import pandas as pd
from tqdm import tqdm

import afft.database as db

from afft.utils.log import logger

from .types import IngestTableResult, IngestTablesCommand


def run_ingest_tables(command: IngestTablesCommand) -> None:
    """Read CSV files from a directory and ingest each as a database table."""
    engine: db.Engine | str = db.create_engine(
        database=command.database,
        host=command.host,
        port=command.port,
        username=requireenv("PG_USERNAME"),
        password=requireenv("PG_PASSWORD"),
    )

    assert isinstance(engine, db.Engine), (
        f"error while connecting to engine: {engine}"
    )

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
        df: pd.DataFrame = pd.read_csv(
            file, parse_dates=list(command.timestamp_columns)
        )
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
