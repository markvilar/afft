"""Runner for the tide correction task."""

import numpy as np
import pandas as pd

from afft.utils.log import logger

from .types import TideCorrectCommand
from .types import TideCorrectConfig
from .types import TideCorrectData


def run_tide_correction(
    command: TideCorrectCommand,
    config: TideCorrectConfig = TideCorrectConfig(),
) -> None:
    """Read pressure and sea level CSVs, apply tide correction, write output."""
    readings = pd.read_csv(command.reading_file, index_col=0).reset_index(
        drop=True
    )
    sealevels = pd.read_csv(command.sealevel_file)

    if command.verbose:
        logger.debug(
            f"Pressure readings: {len(readings)} rows from {command.reading_file}"
        )
        logger.debug(
            f"Sea level values:  {len(sealevels)} rows from {command.sealevel_file}"
        )

    data = TideCorrectData(readings=readings, sealevels=sealevels)
    result = _apply_tide_correction(data, config, verbose=command.verbose)

    result.to_csv(command.output_file, index=False)

    if command.verbose:
        logger.debug(f"Output written to {command.output_file}")


def _validate_tide_coverage(
    readings: pd.DataFrame,
    sealevels: pd.DataFrame,
    config: TideCorrectConfig,
    max_gap: pd.Timedelta = pd.Timedelta(hours=1),
    verbose: bool = False,
) -> None:
    pressure_times = pd.to_datetime(
        readings[config.pressure_timestamp_col],
        format=config.pressure_timestamp_format,
    )
    tide_times = pd.to_datetime(
        sealevels[config.tide_timestamp_col],
        format=config.tide_timestamp_format,
    ).sort_values()

    if verbose:
        logger.debug(
            f"Pressure time range: {pressure_times.min()} to {pressure_times.max()}"
        )
        logger.debug(
            f"Tide time range:     {tide_times.iloc[0]} to {tide_times.iloc[-1]}"
        )

    pressure_ns = pressure_times.astype(np.int64).to_numpy()
    tide_ns = tide_times.astype(np.int64).to_numpy()
    max_gap_ns = int(max_gap.total_seconds() * 1e9)

    # For each pressure timestamp find the nearest tide timestamp via searchsorted
    indices = np.searchsorted(tide_ns, pressure_ns)
    before = np.abs(
        pressure_ns - tide_ns[np.clip(indices - 1, 0, len(tide_ns) - 1)]
    )
    after = np.abs(pressure_ns - tide_ns[np.clip(indices, 0, len(tide_ns) - 1)])
    nearest = np.minimum(before, after)

    exceeds = nearest > max_gap_ns
    if exceeds.any():
        first = pressure_times.iloc[np.argmax(exceeds)]
        gap = nearest[np.argmax(exceeds)] / 1e9 / 60
        raise ValueError(
            f"pressure reading at {first} has no sea level value within "
            f"{max_gap}, nearest is {gap:.1f} minutes away"
        )

    if verbose:
        max_gap_found = nearest.max() / 1e9 / 60
        logger.debug(
            f"Tide coverage valid (max gap: {max_gap_found:.1f} minutes)"
        )


def _apply_tide_correction(
    data: TideCorrectData,
    config: TideCorrectConfig,
    verbose: bool = False,
) -> pd.DataFrame:
    _validate_tide_coverage(
        data.readings, data.sealevels, config, verbose=verbose
    )
    sea_level = _interpolate_sea_level(data.readings, data.sealevels, config)
    result = data.readings.copy()
    result["sea_level"] = sea_level
    result["corrected_depth"] = result[config.pressure_depth_col] - sea_level
    return result


def _interpolate_sea_level(
    readings: pd.DataFrame,
    sealevels: pd.DataFrame,
    config: TideCorrectConfig,
) -> pd.Series:
    pressure_times = pd.to_datetime(
        readings[config.pressure_timestamp_col],
        format=config.pressure_timestamp_format,
    ).astype(np.int64)

    tide_times = pd.to_datetime(
        sealevels[config.tide_timestamp_col],
        format=config.tide_timestamp_format,
    ).astype(np.int64)

    interpolated = np.interp(
        pressure_times.to_numpy(),
        tide_times.to_numpy(),
        sealevels[config.tide_sea_level_col].to_numpy(),
    )

    return pd.Series(interpolated, index=readings.index, name="sea_level")
