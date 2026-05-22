"""Data types for telemetry processing."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProcessorSpec:
    processor: str
    inputs: tuple[str, ...]
    output: str
    config: Any = field(default=None)


@dataclass(slots=True, frozen=True)
class PipelineConfig:
    specs: tuple[ProcessorSpec, ...]
