"""Tests for SEABED localizer config parsing and IO."""

from pathlib import Path

import pytest

from afft.seabed import (
    SeabedLocalizerConfig,
    parse_localizer_config,
    read_localizer_config,
    write_localizer_config,
)

SAMPLE_CFG: str = """\
################################################################################
#               Configuration File for the Seabed Localiser                    #
################################################################################

# WA site preset (commented out — ignored)
#LONGITUDE 115.44043
#LATITUDE -32.02058

# Leftover active preset (overwritten by the last active pair)
LONGITUDE 114.535954
LATITUDE -29.948109

# Active deployment origin
LONGITUDE  113.94725
LATITUDE  -28.81372

VERBOSITY 0
USE_EKF true
USE_ATT_SOURCE "DVL"
LOG_RELATIVE_POSE_INNOVATIONS true

#---------------------------------------#
# AUV Sensor Configuration              #
#---------------------------------------#

# Depth sensor pose (translation only)
DEPTH_SENSOR_POSE_X  0.4   # FIXME: measure this value
DEPTH_SENSOR_POSE_Y  0.0
DEPTH_SENSOR_POSE_Z  -0.23

# DVL pose
DVL_POSE_X      0.0
DVL_POSE_Y      0.0
DVL_POSE_Z      0.0
DVL_POSE_PHI    0.0
DVL_POSE_THETA  3.141592653
DVL_POSE_PSI    -1.570796327

# DeltaT pose with multiple inline comment alternates
DELTAT_POSE_X      0.588   # 0.0 # 0.59
DELTAT_POSE_Y      0.250   # 0.0 # 0.025
DELTAT_POSE_Z      0.048
DELTAT_POSE_PHI    0.0076
DELTAT_POSE_THETA  0.084
DELTAT_POSE_PSI    -3.125

#---------------------------------------#
# Ship Sensor Configuration             #
#---------------------------------------#

# Commented-out alternate transceiver preset (ignored)
#USBL_TRANSCEIVER_POSE_X -3.16249350
#USBL_TRANSCEIVER_POSE_Y 6.99607807

USBL_TRANSCEIVER_POSE_X     -5.715
USBL_TRANSCEIVER_POSE_Y     -1.258
USBL_TRANSCEIVER_POSE_Z      1.352
USBL_TRANSCEIVER_POSE_PHI    0.3316
USBL_TRANSCEIVER_POSE_THETA  0.0
USBL_TRANSCEIVER_POSE_PSI    0.0
"""


def _write_cfg(directory: Path, contents: str) -> Path:
    """Writes localizer config contents into a temp file and returns path."""
    path = directory / "sample.SEABED.localiser.cfg"
    path.write_text(contents)
    return path


def test_parse_populates_origin_and_sections(tmp_path: Path) -> None:
    path = _write_cfg(tmp_path, SAMPLE_CFG)

    config = parse_localizer_config(path)

    # Last active origin pair wins; commented and earlier presets ignored.
    assert config.origin.latitude == -28.81372
    assert config.origin.longitude == 113.94725

    auv_labels = [pose.label for pose in config.auv_sensors.sensor_poses]
    assert auv_labels == ["depth_sensor", "dvl", "deltat"]

    ship_labels = [pose.label for pose in config.ship_sensors.sensor_poses]
    assert ship_labels == ["usbl_transceiver"]


def test_pose_grouping_and_zero_fill(tmp_path: Path) -> None:
    path = _write_cfg(tmp_path, SAMPLE_CFG)

    config = parse_localizer_config(path)
    poses = {p.label: p for p in config.auv_sensors.sensor_poses}

    # Translation-only DEPTH_SENSOR zero-fills the rotation components.
    depth = poses["depth_sensor"]
    assert (depth.locx, depth.locy, depth.locz) == (0.4, 0.0, -0.23)
    assert (depth.rotx, depth.roty, depth.rotz) == (0.0, 0.0, 0.0)

    # DELTAT keeps only the first value, never the commented alternates.
    deltat = poses["deltat"]
    assert deltat.locx == 0.588
    assert deltat.locy == 0.250
    assert deltat.rotz == -3.125


def test_usbl_lands_in_ship_section(tmp_path: Path) -> None:
    path = _write_cfg(tmp_path, SAMPLE_CFG)

    config = parse_localizer_config(path)

    usbl = config.ship_sensors.sensor_poses[0]
    assert usbl.label == "usbl_transceiver"
    assert (usbl.locx, usbl.locy, usbl.locz) == (-5.715, -1.258, 1.352)
    assert usbl.rotx == 0.3316


def test_innovation_key_not_mistaken_for_pose(tmp_path: Path) -> None:
    path = _write_cfg(tmp_path, SAMPLE_CFG)

    config = parse_localizer_config(path)

    # LOG_RELATIVE_POSE_INNOVATIONS must not surface as a sensor pose.
    labels = [p.label for p in config.auv_sensors.sensor_poses]
    assert "log_relative" not in labels


def test_missing_banner_and_origin_raise_aggregated(tmp_path: Path) -> None:
    contents = "VERBOSITY 0\nUSE_EKF true\n"
    path = _write_cfg(tmp_path, contents)

    with pytest.raises(ValueError) as excinfo:
        parse_localizer_config(path)

    message = str(excinfo.value)
    assert "AUV Sensor Configuration" in message
    assert "Ship Sensor Configuration" in message
    assert "LATITUDE" in message
    assert "LONGITUDE" in message


def test_duplicate_pose_component_raises(tmp_path: Path) -> None:
    contents = SAMPLE_CFG.replace(
        "DVL_POSE_Y      0.0", "DVL_POSE_Y      0.0\nDVL_POSE_X      9.9"
    )
    path = _write_cfg(tmp_path, contents)

    with pytest.raises(ValueError):
        parse_localizer_config(path)


def test_io_round_trips(tmp_path: Path) -> None:
    path = _write_cfg(tmp_path, SAMPLE_CFG)
    config = parse_localizer_config(path)

    toml_path = tmp_path / "config.toml"
    write_localizer_config(toml_path, config)
    restored = read_localizer_config(toml_path)

    assert isinstance(restored, SeabedLocalizerConfig)
    assert restored == config
