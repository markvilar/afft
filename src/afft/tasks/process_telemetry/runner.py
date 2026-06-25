"""Runner for the process telemetry task."""

from pathlib import Path

import pandas as pd

from afft.telemetry_processing import run_pipeline, TelemetryPipelineContext
from afft.utils.log import logger

from .config import load_pipeline_config
from .grouping import FileGrouping, FileGrouper, create_file_grouper
from .types import ProcessTelemetryCommand


def run_process_telemetry(command: ProcessTelemetryCommand) -> None:
    """Load CSVs from source_dir, run the telemetry pipeline, write outputs."""
    pipeline_config = load_pipeline_config(command.config_file)

    files: list[Path] = sorted(command.source_dir.glob(command.pattern))
    if not files:
        raise FileNotFoundError(
            f"no files matching '{command.pattern}' in {command.source_dir}"
        )

    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )

    grouper: FileGrouper = create_file_grouper(command.strategy)
    grouping: FileGrouping = grouper(files)

    logger.info(
        f"processing {grouping.label!r}: {len(grouping.files)} table(s)"
    )

    def _read(path: Path) -> pd.DataFrame:
        df = pd.read_csv(path)
        if command.timestamp_column in df.columns:
            df[command.timestamp_column] = pd.to_datetime(
                df[command.timestamp_column],
                format=command.timestamp_format,
                utc=True,
            )
        return df

    context = TelemetryPipelineContext(
        {key: _read(path) for key, path in grouping.files.items()}
    )
    context = run_pipeline(context, pipeline_config)

    output_names: set[str] = {spec.output for spec in pipeline_config.specs}
    prefix: str = f"{grouping.label}_" if grouping.label else ""
    for name in output_names:
        df = context.get_table(name)
        dest = command.output_dir / f"{prefix}{name}.csv"
        df.to_csv(dest, index=False)
        logger.info(f"  {name}: {len(df)} rows → {dest}")
