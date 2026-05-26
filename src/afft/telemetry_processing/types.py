"""Data types for telemetry processing."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(slots=True)
class TelemetryPipelineContext:
    """Keyed store of DataFrames threaded through a processing pipeline."""

    tables: dict[str, pd.DataFrame]

    def has_table(self, name: str) -> bool:
        return name in self.tables

    def get_table(self, name: str) -> pd.DataFrame:
        if not self.has_table(name):
            raise KeyError(f"missing table in context: {name!r}")
        return self.tables[name]

    def set_table(self, name: str, df: pd.DataFrame) -> None:
        self.tables[name] = df

    def extract(self, names: tuple[str, ...]) -> list[pd.DataFrame]:
        missing = [n for n in names if not self.has_table(n)]
        if missing:
            raise KeyError(f"missing table(s) in context: {missing}")
        return [self.get_table(n) for n in names]


@dataclass(slots=True)
class TelemetryProcessorSpec:
    processor: str
    inputs: tuple[str, ...]
    output: str
    config: Any = field(default=None)


@dataclass(slots=True, frozen=True)
class TelemetryPipelineConfig:
    specs: tuple[TelemetryProcessorSpec, ...]
