"""File grouping strategies for the process telemetry task."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable


class GroupingStrategy(StrEnum):
    PREFIX = "prefix"
    SUFFIX = "suffix"


@dataclass(slots=True, frozen=True)
class FileGrouping:
    label: str
    strategy: GroupingStrategy
    files: dict[str, Path]


type FileGrouper = Callable[[list[Path]], FileGrouping]


def _common_prefix(stems: list[str]) -> str:
    """Longest token-aligned prefix shared by ALL stems."""
    tokens_list: list[list[str]] = [s.split("_") for s in stems]
    min_len: int = min(len(t) for t in tokens_list)
    common: list[str] = []
    for i in range(min_len):
        token: str = tokens_list[0][i]
        if all(t[i] == token for t in tokens_list):
            common.append(token)
        else:
            break
    return "_".join(common)


def _common_suffix(stems: list[str]) -> str:
    """Longest token-aligned suffix shared by ALL stems."""
    tokens_list: list[list[str]] = [s.split("_") for s in stems]
    min_len: int = min(len(t) for t in tokens_list)
    common: list[str] = []
    for i in range(1, min_len + 1):
        token: str = tokens_list[0][-i]
        if all(t[-i] == token for t in tokens_list):
            common.insert(0, token)
        else:
            break
    return "_".join(common)


def _group_by_common_prefix(files: list[Path]) -> FileGrouping:
    if len(files) < 2:
        raise ValueError(
            f"prefix grouping requires at least 2 files, got {len(files)}"
        )
    stems: list[str] = [f.stem for f in files]
    label: str = _common_prefix(stems)
    if not label:
        raise ValueError(f"files share no common token-aligned prefix: {stems}")
    stem_to_file: dict[str, Path] = dict(zip(stems, files))
    file_map: dict[str, Path] = {
        stem[len(label) + 1 :]: path for stem, path in stem_to_file.items()
    }
    return FileGrouping(
        label=label, strategy=GroupingStrategy.PREFIX, files=file_map
    )


def _group_by_common_suffix(files: list[Path]) -> FileGrouping:
    if len(files) < 2:
        raise ValueError(
            f"suffix grouping requires at least 2 files, got {len(files)}"
        )
    stems: list[str] = [f.stem for f in files]
    label: str = _common_suffix(stems)
    if not label:
        raise ValueError(f"files share no common token-aligned suffix: {stems}")
    stem_to_file: dict[str, Path] = dict(zip(stems, files))
    file_map: dict[str, Path] = {
        stem[: -(len(label) + 1)]: path for stem, path in stem_to_file.items()
    }
    return FileGrouping(
        label=label, strategy=GroupingStrategy.SUFFIX, files=file_map
    )


def create_file_grouper(strategy: GroupingStrategy) -> FileGrouper:
    """Return a file grouper for the given strategy.

    PREFIX: all files must share a common token-aligned prefix.
      label="qdch0ftq_20120430_002423", key="dvl_teledyne"

    SUFFIX: all files must share a common token-aligned suffix.
      label="dvl_teledyne", key="qdch0ftq_20120430_002423"
    """
    match strategy:
        case GroupingStrategy.PREFIX:
            return _group_by_common_prefix
        case GroupingStrategy.SUFFIX:
            return _group_by_common_suffix
        case _:
            raise ValueError(f"unknown grouping strategy: {strategy!r}")
