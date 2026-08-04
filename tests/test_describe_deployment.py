"""Tests for the describe deployment task and its CLI."""

from pathlib import Path

import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    collect_deployment_files,
    read_deployment_descriptors,
)
from afft.seabed import parse_system_config
from afft.tasks.deployment_descriptor import (
    DescribeDeploymentCommand,
    DescribeDeploymentDiagnostics,
    build_deployment_file_section,
    build_deployment_metadata,
    build_system_section,
    build_telemetry_section,
    run_describe_deployment,
)

DEPLOYMENT_NAME: str = "qd66hv_20170525_234600_deployment_data"
DEPLOYMENT_LABEL: str = "qd66hv_20170525_234600"

SYSCFG: str = """\
BEGIN: syscfg
  vehicle_name:   SEABED
  vehicle_cfg:    NORM_CFG
END: syscfg

BEGIN: sensors
RDI          SIO_rdi         1    SERIAL /dev/ttyS1     57600  N 8 1 NONE
VIS          SIO_vis         1    NETWORK_TCPIP 4040 172.16.154.220
END: sensors

BEGIN: logger
log_dir: /files1/Log
log_to_disk: SYSLOG,RAW,CTL
END: logger
"""

LOCALISER_CFG: str = """\
LONGITUDE  113.94725
LATITUDE  -28.81372

#---------------------------------------#
# AUV Sensor Configuration              #
#---------------------------------------#
DVL_POSE_X  0.0
DVL_POSE_Y  0.0
DVL_POSE_Z  0.0

#---------------------------------------#
# Ship Sensor Configuration             #
#---------------------------------------#
USBL_TRANSCEIVER_POSE_X  -5.715
USBL_TRANSCEIVER_POSE_Y  -1.258
USBL_TRANSCEIVER_POSE_Z   1.352
"""

MAGVAR_CFG: str = """\
MAG_VAR_LAT -32.02058
MAG_VAR_LNG 115.44043
MAGNETIC_VAR_DEG -1.75
"""

MISSION_LOG: str = """\
2017/05/25 23:46:00 Starting mission
Mission File : SS11_snapperbank.mp
Campaign Dir: ./WA201705
"""

RAW_AUV: str = """\
RDI: 1495756000.0 1.0 2.0
VIS: 1495756001.0 image_left.tif
GPS_RMC: 1495756002.0 -32.0 115.5
RDI: 1495756003.0 1.1 2.1
"""

DEPLOYMENT_CONTENTS: dict[str, str] = {
    "messages/20170525_2346.SEABED.syscfg": SYSCFG,
    "messages/20170525_2346.SEABED.localiser.cfg": LOCALISER_CFG,
    "messages/20170525_2346.magnetic_variation.cfg": MAGVAR_CFG,
    "messages/20170525_2347.SS11_snapperbank.dat.log": MISSION_LOG,
    "messages/20170525_2346.RAW.auv": RAW_AUV,
    "usbl/log-20170525-234333.txt": "",
    "camera_calibration/renav20170526/usyd_pool.calib": "",
    "camera_poses/renav20170526_stereo_pose_est.data": "",
}


def _build_deployment(
    root: Path,
    contents: dict[str, str],
    name: str = DEPLOYMENT_NAME,
) -> Path:
    """Builds a synthetic deployment directory tree and returns its root."""
    directory = root / name
    for relative_path, text in contents.items():
        path = directory / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return directory


def _without(*keys: str) -> dict[str, str]:
    """Returns the deployment contents minus the given relative paths."""
    return {
        key: value
        for key, value in DEPLOYMENT_CONTENTS.items()
        if key not in keys
    }


@pytest.fixture
def diagnostics() -> DescribeDeploymentDiagnostics:
    return DescribeDeploymentDiagnostics()


def test_build_file_section_uses_relative_paths(tmp_path: Path) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_CONTENTS)

    section = build_deployment_file_section(collect_deployment_files(directory))

    assert section.system_config == ["messages/20170525_2346.SEABED.syscfg"]
    assert section.raw_messages == ["messages/20170525_2346.RAW.auv"]
    assert section.camera_calibrations == [
        "camera_calibration/renav20170526/usyd_pool.calib"
    ]
    assert section.usbl_logs == ["usbl/log-20170525-234333.txt"]


def test_build_file_section_empties_absent_optional_roles(
    tmp_path: Path,
) -> None:
    directory = _build_deployment(
        tmp_path,
        _without("messages/20170525_2346.magnetic_variation.cfg"),
    )

    section = build_deployment_file_section(collect_deployment_files(directory))

    assert section.magvar_config == []


def test_build_system_section(tmp_path: Path) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_CONTENTS)
    files = collect_deployment_files(directory)
    system_config = parse_system_config(files.system_config)

    system = build_system_section(system_config)

    assert system.vehicle_name == "SEABED"
    assert system.vehicle_config == "NORM_CFG"
    assert system.log_directory == "/files1/Log"
    assert system.logged_streams == ["SYSLOG", "RAW", "CTL"]
    assert system.sensors == ["RDI", "VIS"]


def test_build_telemetry_section_collects_topics(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_CONTENTS)

    section = build_telemetry_section(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    assert section.topics == ["GPS_RMC", "RDI", "VIS"]
    assert diagnostics.warnings == []


def test_build_telemetry_section_warns_on_empty_raw_log(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    contents = dict(DEPLOYMENT_CONTENTS)
    contents["messages/20170525_2346.RAW.auv"] = "no topics here\n"
    directory = _build_deployment(tmp_path, contents)

    section = build_telemetry_section(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    assert section.topics == []
    assert "no message topics" in diagnostics.warnings[0].message


def test_build_metadata_from_log_and_magvar(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    directory = _build_deployment(tmp_path, DEPLOYMENT_CONTENTS)

    metadata = build_deployment_metadata(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    assert metadata.acfr_deployment_label == "SS11_snapperbank"
    assert metadata.acfr_campaign_label == "WA201705"
    assert metadata.origin_latitude == -32.02058
    assert metadata.origin_longitude == 115.44043
    assert metadata.magnetic_variation == -1.75
    assert metadata.acfr_platform_label == ""
    assert diagnostics.warnings == []


def test_build_metadata_warns_on_missing_magvar(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    directory = _build_deployment(
        tmp_path, _without("messages/20170525_2346.magnetic_variation.cfg")
    )

    metadata = build_deployment_metadata(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    assert metadata.origin_latitude == 0.0
    assert [warning.message for warning in diagnostics.warnings] == [
        "no magnetic variation config"
    ]


def test_build_metadata_warns_on_unmatched_magvar_pattern(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    contents = dict(DEPLOYMENT_CONTENTS)
    contents["messages/20170525_2346.magnetic_variation.cfg"] = (
        "MAG_VAR_LAT -32.02058\n"
    )
    directory = _build_deployment(tmp_path, contents)

    metadata = build_deployment_metadata(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    # The file is authoritative, so an unmatched key warns rather than
    # silently yielding 0.0.
    assert metadata.origin_latitude == -32.02058
    assert metadata.origin_longitude == 0.0
    assert metadata.magnetic_variation == 0.0
    messages = [warning.message for warning in diagnostics.warnings]
    assert any("MAG_VAR_LNG" in message for message in messages)
    assert any("MAGNETIC_VAR_DEG" in message for message in messages)


def test_build_metadata_warns_on_missing_mission_log(
    tmp_path: Path,
    diagnostics: DescribeDeploymentDiagnostics,
) -> None:
    directory = _build_deployment(
        tmp_path, _without("messages/20170525_2347.SS11_snapperbank.dat.log")
    )

    metadata = build_deployment_metadata(
        collect_deployment_files(directory), DEPLOYMENT_LABEL, diagnostics
    )

    assert metadata.acfr_deployment_label == ""
    assert metadata.acfr_campaign_label == ""
    assert [warning.message for warning in diagnostics.warnings] == [
        "no mission log file"
    ]


def test_run_writes_descriptor_toml(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _build_deployment(root, DEPLOYMENT_CONTENTS)
    output_file = tmp_path / "deployments.toml"

    result = run_describe_deployment(
        DescribeDeploymentCommand(root_dir=root, output_file=output_file)
    )

    assert result.diagnostics.failures == []
    descriptors = read_deployment_descriptors(output_file)
    assert len(descriptors) == 1

    descriptor = descriptors[0]
    assert descriptor == result.descriptors[0]
    assert descriptor.deployment_label == DEPLOYMENT_LABEL
    assert descriptor.deployment_datetime.isoformat() == (
        "2017-05-25T23:46:00+00:00"
    )
    assert descriptor.telemetry.topics == ["GPS_RMC", "RDI", "VIS"]
    assert descriptor.platform.sensors == []
    assert descriptor.system.sensors == ["RDI", "VIS"]
    assert descriptor.system.vehicle_name == "SEABED"
    assert descriptor.metadata.acfr_campaign_label == "WA201705"
    assert descriptor.files.localizer_config == [
        "messages/20170525_2346.SEABED.localiser.cfg"
    ]


def test_run_leaves_curated_slots_absent(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _build_deployment(root, DEPLOYMENT_CONTENTS)
    output_file = tmp_path / "deployments.toml"

    run_describe_deployment(
        DescribeDeploymentCommand(root_dir=root, output_file=output_file)
    )

    contents = output_file.read_text()
    assert "[deployments.platform]" in contents
    assert "[deployments.vessel]" in contents
    assert "identity" not in contents
    assert "extrinsics" not in contents


def test_run_skips_deployment_with_missing_localizer_config(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    _build_deployment(root, DEPLOYMENT_CONTENTS)
    _build_deployment(
        root,
        _without("messages/20170525_2346.SEABED.localiser.cfg"),
        name="qd66hv_20170526_101500_deployment_data",
    )
    output_file = tmp_path / "deployments.toml"

    result = run_describe_deployment(
        DescribeDeploymentCommand(root_dir=root, output_file=output_file)
    )

    assert [
        failure.deployment_label for failure in result.diagnostics.failures
    ] == ["qd66hv_20170526_101500"]
    assert "localizer_config" in result.diagnostics.failures[0].reason
    # The healthy deployment is still written.
    assert [
        d.deployment_label for d in read_deployment_descriptors(output_file)
    ] == [DEPLOYMENT_LABEL]


def test_run_skips_deployment_with_unparseable_localizer_config(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    contents = dict(DEPLOYMENT_CONTENTS)
    contents["messages/20170525_2346.SEABED.localiser.cfg"] = "VERBOSITY 0\n"
    _build_deployment(root, contents)
    output_file = tmp_path / "deployments.toml"

    result = run_describe_deployment(
        DescribeDeploymentCommand(root_dir=root, output_file=output_file)
    )

    assert len(result.diagnostics.failures) == 1
    assert result.descriptors == []


def test_run_warns_on_uncategorized_files(tmp_path: Path) -> None:
    root = tmp_path / "root"
    contents = dict(DEPLOYMENT_CONTENTS)
    contents["messages/20170525_2346.CTL.auv"] = ""
    _build_deployment(root, contents)
    output_file = tmp_path / "deployments.toml"

    result = run_describe_deployment(
        DescribeDeploymentCommand(root_dir=root, output_file=output_file)
    )

    messages = [warning.message for warning in result.diagnostics.warnings]
    assert any("uncategorized" in message for message in messages)


def test_cli_describe_writes_output(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _build_deployment(root, DEPLOYMENT_CONTENTS)
    output_file = tmp_path / "deployments.toml"

    result: Result = CliRunner().invoke(
        cli,
        [
            "deployment",
            "describe",
            "--input",
            str(root),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert len(read_deployment_descriptors(output_file)) == 1


def test_cli_describe_exits_non_zero_on_failure(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _build_deployment(root, DEPLOYMENT_CONTENTS)
    _build_deployment(
        root,
        _without("messages/20170525_2346.SEABED.syscfg"),
        name="qd66hv_20170526_101500_deployment_data",
    )
    output_file = tmp_path / "deployments.toml"

    result: Result = CliRunner().invoke(
        cli,
        [
            "deployment",
            "describe",
            "--input",
            str(root),
            "--output",
            str(output_file),
            "--verbose",
        ],
    )

    assert result.exit_code == 1
    # The successful deployment is still written.
    assert len(read_deployment_descriptors(output_file)) == 1
