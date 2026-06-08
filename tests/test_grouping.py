"""Tests for the file grouping strategies."""

from pathlib import Path

import pytest

from afft.tasks.process_telemetry.grouping import (
    GroupingStrategy,
    create_file_grouper,
)


def _paths(stems: list[str]) -> list[Path]:
    return [Path(f"/data/{s}.csv") for s in stems]


# --- PREFIX ---


def test_prefix_common_label() -> None:
    files = _paths(
        [
            "qd61g27j_20100421_022145_dvl_teledyne",
            "qd61g27j_20100421_022145_gps_navsol",
            "qd61g27j_20100421_022145_gps_other",
            "qd61g27j_20100421_022145_pressure",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.PREFIX)
    grouping = grouper(files)

    assert grouping.label == "qd61g27j_20100421_022145"
    assert grouping.strategy == GroupingStrategy.PREFIX
    assert set(grouping.files.keys()) == {
        "dvl_teledyne",
        "gps_navsol",
        "gps_other",
        "pressure",
    }


def test_prefix_single_file_raises() -> None:
    files = _paths(["qd61g27j_20100421_022145_dvl_teledyne"])
    grouper = create_file_grouper(GroupingStrategy.PREFIX)
    with pytest.raises(ValueError, match="at least 2 files"):
        grouper(files)


def test_prefix_no_common_prefix_raises() -> None:
    files = _paths(
        [
            "qd61g27j_20100421_dvl_teledyne",
            "abc123_20100501_gps_navsol",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.PREFIX)
    with pytest.raises(ValueError, match="no common token-aligned prefix"):
        grouper(files)


def test_prefix_paths_preserved() -> None:
    files = _paths(
        [
            "dep_20100421_dvl",
            "dep_20100421_gps",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.PREFIX)
    grouping = grouper(files)

    assert grouping.files["dvl"] == Path("/data/dep_20100421_dvl.csv")
    assert grouping.files["gps"] == Path("/data/dep_20100421_gps.csv")


# --- SUFFIX ---


def test_suffix_common_label() -> None:
    files = _paths(
        [
            "dep_a_dvl_teledyne",
            "dep_b_dvl_teledyne",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.SUFFIX)
    grouping = grouper(files)

    assert grouping.label == "dvl_teledyne"
    assert grouping.strategy == GroupingStrategy.SUFFIX
    assert set(grouping.files.keys()) == {"dep_a", "dep_b"}


def test_suffix_no_common_suffix_raises() -> None:
    files = _paths(
        [
            "dep_a_dvl_teledyne",
            "dep_b_gps_navsol",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.SUFFIX)
    with pytest.raises(ValueError, match="no common token-aligned suffix"):
        grouper(files)


def test_suffix_paths_preserved() -> None:
    files = _paths(
        [
            "dep_a_dvl_teledyne",
            "dep_b_dvl_teledyne",
        ]
    )
    grouper = create_file_grouper(GroupingStrategy.SUFFIX)
    grouping = grouper(files)

    assert grouping.files["dep_a"] == Path("/data/dep_a_dvl_teledyne.csv")
    assert grouping.files["dep_b"] == Path("/data/dep_b_dvl_teledyne.csv")


# --- factory ---


def test_unknown_strategy_raises() -> None:
    with pytest.raises(ValueError, match="unknown grouping strategy"):
        create_file_grouper("invalid")  # type: ignore[arg-type]
