"""Tests for the summarize descriptors task and its CLI."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    DeploymentDescriptor,
    DeploymentMetadata,
    DescriptorSummary,
    FileDescriptorSection,
    PlatformDescriptorSection,
    PlatformIdentity,
    PlatformSensor,
    SensorExtrinsics,
    SensorIdentity,
    SystemDescriptorSection,
    TelemetryDescriptorSection,
    VesselDescriptorSection,
    VesselIdentity,
    collect_unfilled_fields,
    summarize_descriptors,
    write_deployment_descriptors,
    write_summary_report,
)
from afft.tasks.deployment_descriptor import (
    SummarizeDescriptorCommand,
    SummarizeDescriptorResult,
    run_summarize_descriptor,
)


def _extrinsics() -> SensorExtrinsics:
    """Builds a filled mounting pose."""
    return SensorExtrinsics(
        locx=0.1, locy=0.2, locz=0.3, rotx=0.0, roty=0.0, rotz=0.0
    )


def _identity(vendor: str = "Teledyne RDI") -> SensorIdentity:
    """Builds a sensor identity, optionally with an empty vendor."""
    return SensorIdentity(
        label="Doppler velocity log",
        vendor=vendor,
        product="Work Horse Navigator",
        type="dvl",
    )


def _build_descriptor(
    label: str,
    moment: datetime,
    campaign: str,
    latitude: float = -28.8,
    longitude: float = 113.9,
    topics: tuple[str, ...] = ("RDI", "GPS_RMC"),
    platform_label: str = "auv-sirius",
    platform: PlatformDescriptorSection | None = None,
    vessel: VesselDescriptorSection | None = None,
) -> DeploymentDescriptor:
    """Builds a descriptor carrying only the fields the summarizer reads."""
    return DeploymentDescriptor(
        deployment_label=label,
        deployment_datetime=moment,
        metadata=DeploymentMetadata(
            acfr_deployment_label=label,
            acfr_campaign_label=campaign,
            acfr_platform_label=platform_label,
            origin_latitude=latitude,
            origin_longitude=longitude,
            magnetic_variation=-1.16,
        ),
        files=FileDescriptorSection(
            raw_messages=["messages/a.RAW.auv"],
            usbl_logs=["usbl/log-1.txt"],
        ),
        telemetry=TelemetryDescriptorSection(topics=list(topics)),
        platform=platform if platform else _enriched_platform(),
        system=SystemDescriptorSection(
            vehicle_name="SEABED",
            vehicle_config="NORM_CFG",
            log_directory="/files1/Log",
            logged_streams=["RAW"],
        ),
        vessel=vessel if vessel else _enriched_vessel(),
    )


def _enriched_platform() -> PlatformDescriptorSection:
    """Builds a fully enriched platform section."""
    return PlatformDescriptorSection(
        identity=PlatformIdentity(
            platform_label="AUV Sirius",
            platform_class="SEABED",
            platform_operator="ACFR",
        ),
        sensors=[
            PlatformSensor(
                key="RDI", identity=_identity(), extrinsics=_extrinsics()
            )
        ],
    )


def _enriched_vessel() -> VesselDescriptorSection:
    """Builds a fully enriched vessel section."""
    return VesselDescriptorSection(
        identity=VesselIdentity(vessel_name="RV Linnaeus"), sensors=[]
    )


def _unenriched_platform() -> PlatformDescriptorSection:
    """Builds a platform section as `describe` leaves it."""
    return PlatformDescriptorSection(
        identity=None, sensors=[PlatformSensor(key="RDI")]
    )


def test_summarize_aggregates_across_deployments() -> None:
    """Counts, ranges, extent, and coverage aggregate over the whole file."""
    descriptors: list[DeploymentDescriptor] = [
        _build_descriptor(
            "aaa_20100428_020202",
            datetime(2010, 4, 28, 2, 2, 2, tzinfo=timezone.utc),
            "WA201004",
            latitude=-28.0,
            longitude=113.0,
            topics=("RDI", "GPS_RMC"),
        ),
        _build_descriptor(
            "bbb_20110415_020103",
            datetime(2011, 4, 15, 2, 1, 3, tzinfo=timezone.utc),
            "WA201104",
            latitude=-30.0,
            longitude=115.0,
            topics=("RDI",),
        ),
    ]

    summary: DescriptorSummary = summarize_descriptors(descriptors)

    assert summary.deployment_count == 2
    assert summary.campaign_counts == {"WA201004": 1, "WA201104": 1}
    assert summary.earliest_datetime.year == 2010
    assert summary.latest_datetime.year == 2011
    assert summary.extent.min_latitude == -30.0
    assert summary.extent.max_latitude == -28.0
    assert summary.extent.min_longitude == 113.0
    assert summary.extent.max_longitude == 115.0
    assert summary.topic_counts == {"RDI": 2, "GPS_RMC": 1}
    assert summary.section_coverage["raw_messages"] == 2
    assert summary.section_coverage["camera_poses"] == 0
    assert summary.enriched
    assert not summary.curation_gaps
    assert len(summary.deployments) == 2


def test_summarize_orders_counts_by_descending_count_then_name() -> None:
    """Ordering is deterministic so report diffs stay quiet."""
    descriptors: list[DeploymentDescriptor] = [
        _build_descriptor(
            "aaa_20100428_020202",
            datetime(2010, 4, 28, tzinfo=timezone.utc),
            "WA201004",
            topics=("ZZZ", "AAA", "RDI"),
        ),
        _build_descriptor(
            "bbb_20110415_020103",
            datetime(2011, 4, 15, tzinfo=timezone.utc),
            "WA201004",
            topics=("RDI",),
        ),
    ]

    summary: DescriptorSummary = summarize_descriptors(descriptors)

    assert list(summary.topic_counts) == ["RDI", "AAA", "ZZZ"]


def test_summarize_reports_unenriched_descriptors() -> None:
    """An un-enriched set is flagged rather than listed gap by gap."""
    descriptors: list[DeploymentDescriptor] = [
        _build_descriptor(
            "aaa_20100428_020202",
            datetime(2010, 4, 28, tzinfo=timezone.utc),
            "WA201004",
            platform_label="",
            platform=_unenriched_platform(),
            vessel=VesselDescriptorSection(),
        )
    ]

    summary: DescriptorSummary = summarize_descriptors(descriptors)

    assert not summary.enriched
    assert not summary.curation_gaps
    assert summary.deployments[0].unfilled_fields


def test_summarize_groups_partially_filled_rosters() -> None:
    """Gaps group by field and carry the deployments they affect."""
    partial = PlatformDescriptorSection(
        identity=PlatformIdentity(
            platform_label="AUV Sirius",
            platform_class="SEABED",
            platform_operator="",
        ),
        sensors=[
            PlatformSensor(
                key="dvl_teledyne_navigator",
                identity=_identity(vendor=""),
                extrinsics=None,
            ),
            PlatformSensor(
                key="sonar_obstacle_avoidance",
                identity=_identity(),
                extrinsics=_extrinsics(),
            ),
        ],
    )
    descriptors: list[DeploymentDescriptor] = [
        _build_descriptor(
            "aaa_20100428_020202",
            datetime(2010, 4, 28, tzinfo=timezone.utc),
            "WA201004",
            platform=partial,
        ),
        _build_descriptor(
            "bbb_20110415_020103",
            datetime(2011, 4, 15, tzinfo=timezone.utc),
            "WA201104",
        ),
    ]

    summary: DescriptorSummary = summarize_descriptors(descriptors)
    gaps: dict[str, list[str]] = {
        gap.field_name: gap.deployment_labels for gap in summary.curation_gaps
    }

    assert summary.enriched
    assert gaps["platform.identity.platform_operator"] == [
        "aaa_20100428_020202"
    ]
    assert gaps["platform.sensors[dvl_teledyne_navigator].identity.vendor"] == [
        "aaa_20100428_020202"
    ]
    assert gaps["platform.sensors[dvl_teledyne_navigator].extrinsics"] == [
        "aaa_20100428_020202"
    ]
    # A fully curated sensor contributes no gap at all.
    assert not any(
        field.startswith("platform.sensors[sonar_obstacle_avoidance]")
        for field in gaps
    )


def test_collect_unfilled_fields_reports_empty_platform_label() -> None:
    """An empty ACFR platform label counts as an unfilled slot."""
    descriptor: DeploymentDescriptor = _build_descriptor(
        "aaa_20100428_020202",
        datetime(2010, 4, 28, tzinfo=timezone.utc),
        "WA201004",
        platform_label="",
    )

    assert "metadata.acfr_platform_label" in collect_unfilled_fields(descriptor)


def test_summarize_rejects_an_empty_set() -> None:
    """Summarizing nothing is a programming error, not an empty summary."""
    with pytest.raises(ValueError):
        summarize_descriptors([])


def test_write_summary_report_is_stable(tmp_path: Path) -> None:
    """The same summary renders byte-identical reports."""
    descriptors: list[DeploymentDescriptor] = [
        _build_descriptor(
            "aaa_20100428_020202",
            datetime(2010, 4, 28, tzinfo=timezone.utc),
            "WA201004",
        )
    ]
    summary: DescriptorSummary = summarize_descriptors(descriptors)

    first: Path = tmp_path / "first.md"
    second: Path = tmp_path / "second.md"
    write_summary_report(first, summary)
    write_summary_report(second, summarize_descriptors(descriptors))

    assert first.read_text() == second.read_text()
    assert first.read_text().startswith("# Deployment Descriptor Summary")
    assert "| Campaign | Deployments |" in first.read_text()


def test_run_summarize_writes_a_report(tmp_path: Path) -> None:
    """With an output path the task writes Markdown and reports the path."""
    input_file: Path = tmp_path / "descriptors.toml"
    output_file: Path = tmp_path / "summary.md"
    write_deployment_descriptors(
        input_file,
        [
            _build_descriptor(
                "aaa_20100428_020202",
                datetime(2010, 4, 28, tzinfo=timezone.utc),
                "WA201004",
            )
        ],
    )

    result: SummarizeDescriptorResult = run_summarize_descriptor(
        SummarizeDescriptorCommand(
            input_file=input_file, output_file=output_file
        )
    )

    assert result.output_file == output_file
    assert output_file.exists()
    assert result.summary.deployment_count == 1


def test_run_summarize_rejects_a_missing_input(tmp_path: Path) -> None:
    """A missing input file fails before anything is read."""
    with pytest.raises(FileNotFoundError):
        run_summarize_descriptor(
            SummarizeDescriptorCommand(input_file=tmp_path / "missing.toml")
        )


def test_run_summarize_rejects_a_missing_output_directory(
    tmp_path: Path,
) -> None:
    """A missing output directory fails before the input is read."""
    input_file: Path = tmp_path / "descriptors.toml"
    write_deployment_descriptors(
        input_file,
        [
            _build_descriptor(
                "aaa_20100428_020202",
                datetime(2010, 4, 28, tzinfo=timezone.utc),
                "WA201004",
            )
        ],
    )

    with pytest.raises(FileNotFoundError):
        run_summarize_descriptor(
            SummarizeDescriptorCommand(
                input_file=input_file,
                output_file=tmp_path / "missing" / "summary.md",
            )
        )


def test_cli_summarize_exits_zero_with_gaps(tmp_path: Path) -> None:
    """Curation gaps are output, not failure, so the command exits zero."""
    input_file: Path = tmp_path / "descriptors.toml"
    write_deployment_descriptors(
        input_file,
        [
            _build_descriptor(
                "aaa_20100428_020202",
                datetime(2010, 4, 28, tzinfo=timezone.utc),
                "WA201004",
                platform_label="",
            )
        ],
    )

    runner = CliRunner()
    result: Result = runner.invoke(
        cli,
        ["deployment", "summarize", "--input", str(input_file), "--verbose"],
    )

    assert result.exit_code == 0, result.output


def test_cli_summarize_writes_a_report(tmp_path: Path) -> None:
    """The CLI passes the output path through to the exporter."""
    input_file: Path = tmp_path / "descriptors.toml"
    output_file: Path = tmp_path / "summary.md"
    write_deployment_descriptors(
        input_file,
        [
            _build_descriptor(
                "aaa_20100428_020202",
                datetime(2010, 4, 28, tzinfo=timezone.utc),
                "WA201004",
            )
        ],
    )

    runner = CliRunner()
    result: Result = runner.invoke(
        cli,
        [
            "deployment",
            "summarize",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()
