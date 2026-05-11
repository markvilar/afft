"""Data types for the message parsing task."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ParseMessageCommand:
    source_file: Path
    config_file: Path
    database: str | None = None
    host: str | None = None
    port: int | None = None
    prefix: str | None = None
    output_dir: Path | None = None


@dataclass(slots=True, frozen=True)
class ParseMessageConfig:
    message_maps: dict[str, str]
    table_names: dict[str, str]
