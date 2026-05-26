"""Runner for the process telemetry task."""

import pandas as pd

from afft.telemetry_processing import run_pipeline, TelemetryPipelineContext
from afft.utils.log import logger

from .config import load_pipeline_config
from .types import ProcessTelemetryCommand


def run_process_telemetry(command: ProcessTelemetryCommand) -> None:
    """Load CSVs from source_dir, run the telemetry pipeline, write outputs."""
    pipeline_config = load_pipeline_config(command.config_file)

    files = sorted(command.source_dir.glob(command.pattern))
    if not files:
        raise FileNotFoundError(
            f"no files matching '{command.pattern}' in {command.source_dir}"
        )

    context = TelemetryPipelineContext({f.stem: pd.read_csv(f) for f in files})
    logger.info(
        f"loaded {len(context.tables)} table(s) from {command.source_dir}"
    )

    context = run_pipeline(context, pipeline_config)

    if not command.output_dir.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_dir}"
        )

    output_names = {spec.output for spec in pipeline_config.specs}
    for name in output_names:
        df = context.get_table(name)
        dest = command.output_dir / f"{name}.csv"
        df.to_csv(dest, index=False)
        logger.info(f"  {name}: {len(df)} rows → {dest}")
