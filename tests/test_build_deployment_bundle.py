"""Tests for the build deployment bundle task and its CLI."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    DeploymentDescriptor,
    DeploymentMetadata,
    FileDescriptorSection,
    PlatformDescriptorSection,
    PlatformIdentity,
    PlatformSensor,
    SystemDescriptorSection,
    TelemetryDescriptorSection,
    VesselDescriptorSection,
    VesselIdentity,
    open_deployment_bundle_reader,
    write_deployment_descriptors,
)
from afft.tasks.build_deployment_bundle import (
    BuildDeploymentBundleCommand,
    BuildDeploymentBundleConfig,
    run_build_deployment_bundle,
)

DEPLOYMENT_LABEL: str = "qdch0ftq_20100428_020202"

_PAROSCI_LINES: list[str] = [
    "PAROSCI:  1272420122.878\t-0.0514",
    "PAROSCI:  1272420123.878\t-0.0523",
]


def _build_descriptor(
    label: str = DEPLOYMENT_LABEL, *, enriched: bool = True
) -> DeploymentDescriptor:
    """Builds a minimal descriptor with one declared platform sensor."""
    platform = PlatformDescriptorSection(
        identity=(
            PlatformIdentity(
                platform_label="AUV Sirius",
                platform_class="SEABED",
                platform_operator="ACFR",
            )
            if enriched
            else None
        ),
        sensors=(
            [PlatformSensor(key="pressure_parosci", message_topics=["PAROSCI"])]
            if enriched
            else []
        ),
    )
    vessel = VesselDescriptorSection(
        identity=(
            VesselIdentity(vessel_name="RV Linnaeus") if enriched else None
        )
    )
    return DeploymentDescriptor(
        deployment_label=label,
        deployment_datetime=datetime(2010, 4, 28, 2, 2, 2, tzinfo=timezone.utc),
        metadata=DeploymentMetadata(
            acfr_deployment_label="geebank_16_15m_out",
            acfr_campaign_label="WA201004",
            acfr_platform_label="",
            origin_latitude=-28.81372,
            origin_longitude=113.94725,
            magnetic_variation=-1.16,
        ),
        files=FileDescriptorSection(),
        telemetry=TelemetryDescriptorSection(topics=["PAROSCI"]),
        platform=platform,
        system=SystemDescriptorSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["RAW"],
            sensors=["PAROSCI"],
        ),
        vessel=vessel,
    )


def _write_data_dir(
    root: Path, label: str, raw_lines: list[str] | None = _PAROSCI_LINES
) -> Path:
    """Builds a minimal deployment data directory."""
    data_dir = root / f"{label}_deployment_data"
    messages_dir = data_dir / "messages"
    messages_dir.mkdir(parents=True)
    (messages_dir / f"{label}.SEABED.syscfg").write_text("")
    (messages_dir / f"{label}.SEABED.localiser.cfg").write_text("")
    if raw_lines is not None:
        (messages_dir / f"{label}.RAW.auv").write_text(
            "\n".join(raw_lines) + "\n"
        )
    return data_dir


def _write_config(root: Path) -> Path:
    config_file = root / "config.toml"
    config_file.write_text(
        "[afft.tasks.build_deployment_bundle.message_map]\n"
        'PAROSCI = "ParosciPressureMessageV1"\n'
    )
    return config_file


def _write_command(
    tmp_path: Path,
    *,
    label: str = DEPLOYMENT_LABEL,
    enriched: bool = True,
    raw_lines: list[str] | None = _PAROSCI_LINES,
) -> BuildDeploymentBundleCommand:
    descriptor_file = tmp_path / "descriptors.toml"
    write_deployment_descriptors(
        descriptor_file, [_build_descriptor(label, enriched=enriched)]
    )
    data_dir = _write_data_dir(tmp_path, label, raw_lines)
    config_file = _write_config(tmp_path)
    return BuildDeploymentBundleCommand(
        descriptor_file=descriptor_file,
        deployment_label=label,
        data_dir=data_dir,
        config_file=config_file,
        output_file=tmp_path / "bundle.h5",
    )


def _config() -> BuildDeploymentBundleConfig:
    return BuildDeploymentBundleConfig(
        message_map={"PAROSCI": "ParosciPressureMessageV1"}
    )


def test_run_builds_a_readable_bundle(tmp_path: Path) -> None:
    command = _write_command(tmp_path)

    result = run_build_deployment_bundle(command, _config())

    assert result.deployment_label == DEPLOYMENT_LABEL
    assert result.diagnostics.warnings == []

    with open_deployment_bundle_reader(command.output_file) as reader:
        assert reader.deployment.identity().deployment_label == (
            DEPLOYMENT_LABEL
        )
        assert reader.platform.identity().platform_label == "AUV Sirius"
        assert reader.vessel.identity().vessel_name == "RV Linnaeus"
        assert reader.telemetry.raw.topics() == [
            ("pressure_parosci", "PAROSCI")
        ]
        frame = reader.telemetry.raw.read("pressure_parosci", "PAROSCI")
        assert len(frame) == 2
        assert frame["depth"].tolist() == pytest.approx([-0.0514, -0.0523])


def test_run_warns_on_a_declared_topic_with_no_messages(
    tmp_path: Path,
) -> None:
    # OAS is not declared by any sensor, so it never reaches the registry --
    # leaving the declared PAROSCI topic with no parsed messages at all.
    oas_line = (
        "OAS:  1272420122.546  ProfRng: 20.00 PseudoAlt: 13.52 "
        "PseudoFwdDistance: 14.14"
    )
    command = _write_command(tmp_path, raw_lines=[oas_line])

    result = run_build_deployment_bundle(command, _config())

    assert [
        (warning.topic, warning.message)
        for warning in result.diagnostics.warnings
    ] == [("PAROSCI", "declared but no messages parsed")]


def test_run_rejects_an_unknown_deployment_label(tmp_path: Path) -> None:
    command = _write_command(tmp_path)
    command = BuildDeploymentBundleCommand(
        descriptor_file=command.descriptor_file,
        deployment_label="does_not_exist",
        data_dir=command.data_dir,
        config_file=command.config_file,
        output_file=command.output_file,
    )

    with pytest.raises(ValueError, match="deployment not found"):
        run_build_deployment_bundle(command, _config())


def test_run_rejects_an_unenriched_descriptor(tmp_path: Path) -> None:
    command = _write_command(tmp_path, enriched=False)

    with pytest.raises(ValueError, match="not enriched"):
        run_build_deployment_bundle(command, _config())


def test_run_rejects_a_data_dir_with_no_raw_messages(tmp_path: Path) -> None:
    command = _write_command(tmp_path, raw_lines=None)

    with pytest.raises(FileNotFoundError, match="no raw message logs"):
        run_build_deployment_bundle(command, _config())


def test_run_rejects_an_existing_output_file(tmp_path: Path) -> None:
    command = _write_command(tmp_path)
    run_build_deployment_bundle(command, _config())

    with pytest.raises(ValueError, match="already exists"):
        run_build_deployment_bundle(command, _config())


def test_cli_builds_a_deployment_bundle(tmp_path: Path) -> None:
    command = _write_command(tmp_path)

    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "build",
            "--descriptor-file",
            str(command.descriptor_file),
            "--deployment-label",
            DEPLOYMENT_LABEL,
            "--data-dir",
            str(command.data_dir),
            "--config",
            str(command.config_file),
            "--output",
            str(command.output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    with open_deployment_bundle_reader(command.output_file) as reader:
        assert reader.telemetry.raw.topics() == [
            ("pressure_parosci", "PAROSCI")
        ]
