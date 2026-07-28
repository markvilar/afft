"""Tests for SEABED system config parsing and IO."""

from pathlib import Path

import pytest

from afft.seabed import (
    SeabedSystemConfig,
    parse_system_config,
    read_system_config,
    write_system_config,
)

SAMPLE_SYSCFG: str = """\
###########################################################
# ROV/AUV System Configuration File
###########################################################
BEGIN: syscfg
#Format: Label:  Value   #comment
  vehicle_name:   SEABED         #JASON|JHU_ROV|ARGO|DSL120|SEABED|ABE
  vehicle_cfg:    NORM_CFG       #NORM_CFG|DEEP_CFG|SHALLOW_CFG
END: syscfg

BEGIN: sensors
#Label  SensorDriver, Vlevel, PortType, Port Params, SensorFile
DELTA_T      SIO_deltaT      1    NETWORK_TCPIP 4040 172.16.154.220
MP_INPUT     SIO_mp          1    NETWORK_UDP  5678 NONE
RDI          SIO_rdi         1    SERIAL /dev/ttyS1     57600  N 8 1 NONE
GPS          SIO_gps         1    SERIAL /dev/ttyS12     9600  N 8 1 NONE
#RDI         SIO_rdi         1    SERIAL /dev/ttyS38    57600  N 8 1 NONE
END: sensors

BEGIN: logger
log_dir: /files1/Log
log_to_disk: SYSLOG,RAW,CTL,AUV,MSG,RDI
bcast 127.0.0.1 12345: AUV,MPD   # to mission planner
default_options: multi no_timestamp hourly
END: logger

BEGIN: oas
range:  30
END: oas
"""


def _write_syscfg(directory: Path, contents: str) -> Path:
    """Writes syscfg contents into a temp file and returns its path."""
    path = directory / "sample.SEABED.syscfg"
    path.write_text(contents)
    return path


def test_parse_populates_all_blocks(tmp_path: Path) -> None:
    path = _write_syscfg(tmp_path, SAMPLE_SYSCFG)

    config = parse_system_config(path)

    assert config.vehicle.vehicle_name == "SEABED"
    assert config.vehicle.vehicle_config == "NORM_CFG"
    assert config.logger.log_dir == "/files1/Log"
    assert config.logger.logged_streams == [
        "SYSLOG",
        "RAW",
        "CTL",
        "AUV",
        "MSG",
        "RDI",
    ]


def test_parse_strips_comments_and_commented_rows(tmp_path: Path) -> None:
    path = _write_syscfg(tmp_path, SAMPLE_SYSCFG)

    config = parse_system_config(path)

    # The commented-out alternate RDI row is ignored; inline comments gone.
    names = [entry.name for entry in config.sensors.entries]
    assert names == ["DELTA_T", "MP_INPUT", "RDI", "GPS"]

    rdi = config.sensors.entries[2]
    assert rdi.driver == "SIO_rdi"
    assert rdi.transport == "SERIAL"

    delta_t = config.sensors.entries[0]
    assert delta_t.transport == "NETWORK_TCPIP"


def test_unknown_blocks_are_skipped(tmp_path: Path) -> None:
    # The 'oas' block in the sample is not modeled and must be dropped.
    path = _write_syscfg(tmp_path, SAMPLE_SYSCFG)

    config = parse_system_config(path)

    assert isinstance(config, SeabedSystemConfig)


def test_missing_block_raises(tmp_path: Path) -> None:
    contents = SAMPLE_SYSCFG.replace("BEGIN: logger", "BEGIN: nope").replace(
        "END: logger", "END: nope"
    )
    path = _write_syscfg(tmp_path, contents)

    with pytest.raises(ValueError):
        parse_system_config(path)


def test_duplicate_block_raises(tmp_path: Path) -> None:
    contents = (
        SAMPLE_SYSCFG + "\nBEGIN: syscfg\n  vehicle_name: X\nEND: syscfg\n"
    )
    path = _write_syscfg(tmp_path, contents)

    with pytest.raises(ValueError):
        parse_system_config(path)


def test_io_round_trips(tmp_path: Path) -> None:
    path = _write_syscfg(tmp_path, SAMPLE_SYSCFG)
    config = parse_system_config(path)

    toml_path = tmp_path / "config.toml"
    write_system_config(toml_path, config)
    restored = read_system_config(toml_path)

    assert restored == config
