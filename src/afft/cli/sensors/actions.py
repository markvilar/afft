"""Actions for sensor-specific processing CLI commands."""

from pathlib import Path

import pandas as pd

from afft.deployment import load_deployment_config
from afft.sensors.usbl_linkquest import process_tracklink_usbl
from afft.utils.log import logger


def dispatch_process_tracklink_usbl(
    usbl_file: str | Path,
    pressure_file: str | Path,
    output_file: str | Path,
    ship_sensor_configs: str | Path,
    deployment_label: str,
) -> None:
    """Resolve positions and estimate uncertainty from TrackLink USBL data."""
    deployment = load_deployment_config(
        Path(ship_sensor_configs), deployment_label
    )
    logger.info(
        f"deployment {deployment.label!r}: {deployment.ship_name}, "
        f"{deployment.date}, sensor_keys={list(deployment.sensor_keys)}"
    )

    usbl: pd.DataFrame = pd.read_csv(Path(usbl_file))
    pressure: pd.DataFrame = pd.read_csv(Path(pressure_file))

    result: pd.DataFrame = process_tracklink_usbl(usbl, pressure)

    output_path: Path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info(f"wrote {len(result)} rows → {output_path}")
