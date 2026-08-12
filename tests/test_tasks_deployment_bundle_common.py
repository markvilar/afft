"""Tests for the common deployment bundle tasks."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    DeploymentIdentity,
    DeploymentProvenance,
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.tasks.build_deployment_bundle import record_to_frame
from afft.tasks.deployment_bundle_common import (
    ClipDeploymentBundleCommand,
    ExportBundleFrameCommand,
    ExportBundleFrameResult,
    IngestBundleFrameCommand,
    IngestBundleFrameResult,
    read_frame_file,
    run_clip_deployment_bundle,
    run_export_bundle_frame,
    run_ingest_bundle_frame,
    validate_bundle_frame_key,
)

SEA_LEVEL_CSV: str = (
    "dt,sea_level,datetime,station,latitude,longitude,atlas\n"
    "1230735600,0.266,2008-12-31 15:00:00+00:00,,-28.8333,114,FES2022\n"
    "1230739200,0.311,2008-12-31 16:00:00.500000+00:00,,-28.8333,114,FES2022\n"
)

SEA_LEVEL_KEY: str = "metocean/worldtides/sealevel"


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    """A CSV shaped as the stored WorldTides sea level series."""
    path: Path = tmp_path / "sea_level.csv"
    path.write_text(SEA_LEVEL_CSV)
    return path


@pytest.fixture
def bundle_file(tmp_path: Path) -> Path:
    """An existing bundle holding one unrelated frame."""
    path: Path = tmp_path / "deployment_bundle.sqlite"
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "telemetry/raw/pressure/messages", pd.DataFrame({"value": [1.0]})
        )
    return path


@pytest.fixture
def populated_bundle_file(bundle_file: Path, source_file: Path) -> Path:
    """A bundle holding the sea level frame, as ingest writes it."""
    run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=source_file,
            datetime_columns=("datetime",),
        )
    )
    return bundle_file


def test_valid_frame_keys_are_accepted() -> None:
    validate_bundle_frame_key(SEA_LEVEL_KEY)
    validate_bundle_frame_key("bundle")
    validate_bundle_frame_key(
        "platform/sensors/usbl_linkquest_transceiver/extrinsics"
    )


@pytest.mark.parametrize(
    "key",
    [
        "",
        "/metocean/worldtides/sealevel",
        "metocean/worldtides/sealevel/",
        "metocean//sealevel",
        "metocean/world tides/sealevel",
        "metocean/worldtides/sea:level",
    ],
)
def test_structurally_invalid_frame_keys_are_rejected(key: str) -> None:
    with pytest.raises(ValueError):
        validate_bundle_frame_key(key)


def test_unknown_frame_keys_are_accepted() -> None:
    """Validation is structural only, so an unrecognised key still passes."""
    validate_bundle_frame_key("metocean/worldtide/sealevel")
    validate_bundle_frame_key("not_a_bundle_section/whatever")


def test_datetime_columns_are_parsed_as_utc(source_file: Path) -> None:
    frame: pd.DataFrame = read_frame_file(source_file, ("datetime",))

    assert isinstance(frame["datetime"].dtype, pd.DatetimeTZDtype)
    assert str(frame["datetime"].dt.tz) == "UTC"


def test_columns_outside_datetime_columns_keep_inferred_dtypes(
    source_file: Path,
) -> None:
    frame: pd.DataFrame = read_frame_file(source_file, ("datetime",))

    assert frame["dt"].dtype == "int64"
    assert frame["sea_level"].dtype == "float64"
    assert frame["atlas"].dtype == object


def test_a_datetime_column_not_in_the_file_is_rejected(
    source_file: Path,
) -> None:
    with pytest.raises(ValueError, match="absent"):
        read_frame_file(source_file, ("absent",))


def test_ingested_frame_is_readable_from_the_bundle(
    bundle_file: Path, source_file: Path
) -> None:
    result: IngestBundleFrameResult = run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=source_file,
            datetime_columns=("datetime",),
        )
    )

    assert result.rows == 2
    with open_deployment_bundle_reader(bundle_file) as reader:
        frame: pd.DataFrame = reader.read_frame(SEA_LEVEL_KEY)

    assert len(frame) == 2
    assert isinstance(frame["datetime"].dtype, pd.DatetimeTZDtype)
    assert frame["sea_level"].to_list() == [0.266, 0.311]


def test_ingestion_leaves_existing_frames_alone(
    bundle_file: Path, source_file: Path
) -> None:
    run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=source_file,
            datetime_columns=("datetime",),
        )
    )

    with open_deployment_bundle_reader(bundle_file) as reader:
        keys: list[str] = reader.list_frames()

    assert "telemetry/raw/pressure/messages" in keys
    assert SEA_LEVEL_KEY in keys


def test_ingesting_over_an_existing_key_is_refused(
    bundle_file: Path, source_file: Path
) -> None:
    command = IngestBundleFrameCommand(
        bundle_file=bundle_file,
        key=SEA_LEVEL_KEY,
        input_file=source_file,
        datetime_columns=("datetime",),
    )
    run_ingest_bundle_frame(command)

    with pytest.raises(ValueError, match="already holds a frame"):
        run_ingest_bundle_frame(command)


def test_overwrite_replaces_an_existing_frame(
    bundle_file: Path, source_file: Path, tmp_path: Path
) -> None:
    run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=source_file,
            datetime_columns=("datetime",),
        )
    )

    replacement: Path = tmp_path / "replacement.csv"
    replacement.write_text("sea_level\n9.0\n")
    run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=replacement,
            overwrite=True,
        )
    )

    with open_deployment_bundle_reader(bundle_file) as reader:
        frame: pd.DataFrame = reader.read_frame(SEA_LEVEL_KEY)

    assert frame["sea_level"].to_list() == [9.0]


def test_a_missing_bundle_is_rejected(
    tmp_path: Path, source_file: Path
) -> None:
    with pytest.raises(FileNotFoundError, match="deployment bundle"):
        run_ingest_bundle_frame(
            IngestBundleFrameCommand(
                bundle_file=tmp_path / "absent.sqlite",
                key=SEA_LEVEL_KEY,
                input_file=source_file,
            )
        )


def test_a_missing_input_file_is_rejected(
    bundle_file: Path, tmp_path: Path
) -> None:
    with pytest.raises(FileNotFoundError, match="input file"):
        run_ingest_bundle_frame(
            IngestBundleFrameCommand(
                bundle_file=bundle_file,
                key=SEA_LEVEL_KEY,
                input_file=tmp_path / "absent.csv",
            )
        )


def test_an_invalid_key_is_rejected_before_the_bundle_is_opened(
    bundle_file: Path, source_file: Path
) -> None:
    with pytest.raises(ValueError, match="leading or trailing slash"):
        run_ingest_bundle_frame(
            IngestBundleFrameCommand(
                bundle_file=bundle_file,
                key="/metocean/worldtides/sealevel",
                input_file=source_file,
            )
        )


def test_cli_ingest_frame_writes_the_frame(
    bundle_file: Path, source_file: Path
) -> None:
    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "ingest-frame",
            "--bundle",
            str(bundle_file),
            "--key",
            SEA_LEVEL_KEY,
            "--file",
            str(source_file),
            "--datetime-column",
            "datetime",
        ],
    )

    assert result.exit_code == 0
    with open_deployment_bundle_reader(bundle_file) as reader:
        assert SEA_LEVEL_KEY in reader.list_frames()


def test_cli_ingest_frame_exits_non_zero_on_a_missing_bundle(
    tmp_path: Path, source_file: Path
) -> None:
    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "ingest-frame",
            "--bundle",
            str(tmp_path / "absent.sqlite"),
            "--key",
            SEA_LEVEL_KEY,
            "--file",
            str(source_file),
        ],
    )

    assert result.exit_code != 0


@pytest.mark.parametrize(
    "suffix, read",
    [
        (".csv", pd.read_csv),
        (".parquet", pd.read_parquet),
        (".feather", pd.read_feather),
        (".json", pd.read_json),
    ],
)
def test_an_exported_frame_reads_back_with_the_bundle_contents(
    populated_bundle_file: Path,
    tmp_path: Path,
    suffix: str,
    read: object,
) -> None:
    """Every supported suffix carries the rows and columns through."""
    output_file: Path = tmp_path / f"exported{suffix}"

    result: ExportBundleFrameResult = run_export_bundle_frame(
        ExportBundleFrameCommand(
            bundle_file=populated_bundle_file,
            key=SEA_LEVEL_KEY,
            output_file=output_file,
        )
    )

    assert result.rows == 2
    assert "sea_level" in result.columns

    frame: pd.DataFrame = read(output_file)  # type: ignore[operator]
    assert len(frame) == 2
    assert frame["sea_level"].to_list() == [0.266, 0.311]


@pytest.mark.parametrize(
    "suffix, read",
    [(".parquet", pd.read_parquet), (".feather", pd.read_feather)],
)
def test_the_binary_formats_preserve_the_timestamp_dtype(
    populated_bundle_file: Path,
    tmp_path: Path,
    suffix: str,
    read: object,
) -> None:
    """Parquet and Feather carry `datetime64[ns, UTC]` in the file, so a
    round trip needs no timestamp handling at all."""
    output_file: Path = tmp_path / f"exported{suffix}"
    run_export_bundle_frame(
        ExportBundleFrameCommand(
            bundle_file=populated_bundle_file,
            key=SEA_LEVEL_KEY,
            output_file=output_file,
        )
    )

    frame: pd.DataFrame = read(output_file)  # type: ignore[operator]

    assert isinstance(frame["datetime"].dtype, pd.DatetimeTZDtype)


def test_an_exported_csv_can_be_ingested_back(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    """The property that keeps export and ingest a pair rather than two
    commands that happen to share a file format."""
    output_file: Path = tmp_path / "exported.csv"
    run_export_bundle_frame(
        ExportBundleFrameCommand(
            bundle_file=populated_bundle_file,
            key=SEA_LEVEL_KEY,
            output_file=output_file,
        )
    )

    run_ingest_bundle_frame(
        IngestBundleFrameCommand(
            bundle_file=populated_bundle_file,
            key=SEA_LEVEL_KEY,
            input_file=output_file,
            datetime_columns=("datetime",),
            overwrite=True,
        )
    )

    with open_deployment_bundle_reader(populated_bundle_file) as reader:
        frame: pd.DataFrame = reader.read_frame(SEA_LEVEL_KEY)

    assert isinstance(frame["datetime"].dtype, pd.DatetimeTZDtype)
    assert frame["datetime"].to_list() == [
        pd.Timestamp("2008-12-31 15:00:00+00:00"),
        pd.Timestamp("2008-12-31 16:00:00.500000+00:00"),
    ]
    assert frame["sea_level"].to_list() == [0.266, 0.311]


def test_an_unsupported_output_suffix_is_rejected(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="unsupported output file suffix"):
        run_export_bundle_frame(
            ExportBundleFrameCommand(
                bundle_file=populated_bundle_file,
                key=SEA_LEVEL_KEY,
                output_file=tmp_path / "exported.xlsx",
            )
        )


def test_a_missing_key_names_the_keys_the_bundle_holds(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    """A bare 'no frame at that key' would turn a typo into a round trip
    through `afft bundle list`."""
    with pytest.raises(ValueError, match="holds no frame") as error:
        run_export_bundle_frame(
            ExportBundleFrameCommand(
                bundle_file=populated_bundle_file,
                key="metocean/worldtides/sea_level",
                output_file=tmp_path / "exported.csv",
            )
        )

    assert SEA_LEVEL_KEY in str(error.value)


def test_exporting_over_an_existing_file_is_refused(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    output_file: Path = tmp_path / "exported.csv"
    output_file.write_text("existing\n")
    command = ExportBundleFrameCommand(
        bundle_file=populated_bundle_file,
        key=SEA_LEVEL_KEY,
        output_file=output_file,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        run_export_bundle_frame(command)

    run_export_bundle_frame(command.model_copy(update={"overwrite": True}))

    assert "sea_level" in output_file.read_text()


def test_an_invalid_export_key_is_rejected_before_the_bundle_is_opened(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="leading or trailing slash"):
        run_export_bundle_frame(
            ExportBundleFrameCommand(
                bundle_file=populated_bundle_file,
                key="/metocean/worldtides/sealevel",
                output_file=tmp_path / "exported.csv",
            )
        )


def test_exporting_leaves_the_bundle_unchanged(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    """The reader interface makes this structural, but the guarantee is
    what callers rely on."""
    before: bytes = populated_bundle_file.read_bytes()

    run_export_bundle_frame(
        ExportBundleFrameCommand(
            bundle_file=populated_bundle_file,
            key=SEA_LEVEL_KEY,
            output_file=tmp_path / "exported.csv",
        )
    )

    assert populated_bundle_file.read_bytes() == before


def test_cli_export_frame_writes_the_file(
    populated_bundle_file: Path, tmp_path: Path
) -> None:
    output_file: Path = tmp_path / "exports" / "exported.csv"

    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "export-frame",
            "--bundle",
            str(populated_bundle_file),
            "--key",
            SEA_LEVEL_KEY,
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.is_file()


def test_cli_export_frame_exits_non_zero_on_a_missing_bundle(
    tmp_path: Path,
) -> None:
    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "export-frame",
            "--bundle",
            str(tmp_path / "absent.sqlite"),
            "--key",
            SEA_LEVEL_KEY,
            "--output",
            str(tmp_path / "exported.csv"),
        ],
    )

    assert result.exit_code != 0


CLIP_LABEL: str = "u4rmk_20231107_043022"


def _clip_source_bundle(path: Path) -> Path:
    """A bundle shaped like a full-grid deployment: identity, provenance, a
    telemetry frame on `timestamp`, a coarse metocean series, and two frames
    with no time axis at all."""
    timestamps = pd.to_datetime(
        [
            "2023-11-07T05:00:00Z",
            "2023-11-07T05:10:00Z",
            "2023-11-07T05:20:00Z",
            "2023-11-07T05:40:00Z",
            "2023-11-07T05:50:00Z",
        ],
        utc=True,
    )
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "deployment/identity",
            record_to_frame(
                DeploymentIdentity(
                    deployment_label=CLIP_LABEL,
                    deployment_start_datetime=datetime(
                        2023, 11, 7, 5, 0, tzinfo=timezone.utc
                    ),
                )
            ),
        )
        bundle.write_frame(
            "deployment/provenance",
            record_to_frame(DeploymentProvenance(deployment_key=CLIP_LABEL)),
        )
        bundle.write_frame(
            "telemetry/raw/depth/PAROSCI/messages",
            pd.DataFrame(
                {"timestamp": timestamps, "depth": [1.0, 2.0, 3.0, 4.0, 5.0]}
            ),
        )
        bundle.write_frame(
            "metocean/stormglass/wave_height",
            pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(
                        ["2023-11-07T00:00:00Z", "2023-11-07T06:00:00Z"],
                        utc=True,
                    ),
                    "wave_height": [1.5, 1.7],
                }
            ),
        )
        bundle.write_frame(
            "platform/sensors/depth/calibration",
            pd.DataFrame({"name": ["scale"], "value": [1.0]}),
        )
        bundle.write_frame(
            "platform/sensors/depth/message_topics",
            pd.DataFrame({"topic": ["PAROSCI"]}),
        )
    return path


@pytest.fixture
def clip_source_file(tmp_path: Path) -> Path:
    return _clip_source_bundle(tmp_path / "full_grid.sqlite")


def _clip_command(
    input_file: Path,
    output_file: Path,
    *,
    start: str = "2023-11-07T05:10:00Z",
    end: str = "2023-11-07T05:40:00Z",
    label_suffix: str = "dense01",
    datetime_column: str = "timestamp",
    no_clip_patterns: tuple[str, ...] = (),
    overwrite: bool = False,
) -> ClipDeploymentBundleCommand:
    return ClipDeploymentBundleCommand(
        input_file=input_file,
        output_file=output_file,
        start=datetime.fromisoformat(start),
        end=datetime.fromisoformat(end),
        label_suffix=label_suffix,
        datetime_column=datetime_column,
        no_clip_patterns=no_clip_patterns,
        overwrite=overwrite,
    )


def test_clip_keeps_only_the_rows_inside_the_window(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """The window is closed: a row at `start` and a row at `end` are both in,
    and the rows outside on either side are not."""
    output_file = tmp_path / "dense_grid.sqlite"

    run_clip_deployment_bundle(_clip_command(clip_source_file, output_file))

    with open_deployment_bundle_reader(output_file) as reader:
        frame = reader.read_frame("telemetry/raw/depth/PAROSCI/messages")

    assert frame["depth"].tolist() == [2.0, 3.0, 4.0]


def test_clip_copies_frames_without_the_datetime_column(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """A frame with no time axis is copied whole, without the task needing to
    know the key exists."""
    output_file = tmp_path / "dense_grid.sqlite"

    result = run_clip_deployment_bundle(
        _clip_command(clip_source_file, output_file)
    )

    with open_deployment_bundle_reader(clip_source_file) as reader:
        expected = reader.read_frame("platform/sensors/depth/calibration")
    with open_deployment_bundle_reader(output_file) as reader:
        actual = reader.read_frame("platform/sensors/depth/calibration")

    pd.testing.assert_frame_equal(actual, expected)
    assert "platform/sensors/depth/calibration" in result.copied_keys
    assert "platform/sensors/depth/message_topics" in result.copied_keys


def test_clip_keeps_every_row_of_a_no_clip_frame(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """A metocean series carries `timestamp` but is sampled far coarser than
    telemetry, so a dense-grid window would leave nothing to interpolate."""
    output_file = tmp_path / "dense_grid.sqlite"

    result = run_clip_deployment_bundle(
        _clip_command(
            clip_source_file,
            output_file,
            no_clip_patterns=("metocean/*",),
        )
    )

    with open_deployment_bundle_reader(output_file) as reader:
        frame = reader.read_frame("metocean/stormglass/wave_height")

    assert len(frame) == 2
    assert "metocean/stormglass/wave_height" in result.copied_keys


def test_clip_copies_a_frame_whose_time_column_is_named_otherwise(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """Rule 2 keys off the column, so naming another one leaves the telemetry
    frame copied whole rather than clipped on a column it does not carry."""
    output_file = tmp_path / "dense_grid.sqlite"

    result = run_clip_deployment_bundle(
        _clip_command(
            clip_source_file, output_file, datetime_column="acquired_at"
        )
    )

    with open_deployment_bundle_reader(output_file) as reader:
        frame = reader.read_frame("telemetry/raw/depth/PAROSCI/messages")

    assert len(frame) == 5
    assert result.clipped_keys == ()


def test_clip_rewrites_the_deployment_identity(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """The clipped bundle is a new deployment and says so."""
    output_file = tmp_path / "dense_grid.sqlite"

    result = run_clip_deployment_bundle(
        _clip_command(clip_source_file, output_file)
    )

    assert result.deployment_label == f"{CLIP_LABEL}_dense01"
    with open_deployment_bundle_reader(output_file) as reader:
        identity = reader.read_frame("deployment/identity")

    assert identity["deployment_label"].iloc[0] == f"{CLIP_LABEL}_dense01"
    assert identity["deployment_start_datetime"].iloc[0] == pd.Timestamp(
        "2023-11-07T05:10:00Z"
    )
    assert identity["deployment_end_datetime"].iloc[0] == pd.Timestamp(
        "2023-11-07T05:40:00Z"
    )


def test_clip_records_its_source_and_window_in_provenance(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """A dense-grid bundle traces back to its full-grid parent without
    external bookkeeping."""
    output_file = tmp_path / "dense_grid.sqlite"

    run_clip_deployment_bundle(_clip_command(clip_source_file, output_file))

    with open_deployment_bundle_reader(output_file) as reader:
        provenance = reader.read_frame("deployment/provenance")

    assert provenance["source_bundle"].iloc[0] == str(clip_source_file)
    assert provenance["clip_start_datetime"].iloc[0] == pd.Timestamp(
        "2023-11-07T05:10:00Z"
    )
    assert provenance["clip_end_datetime"].iloc[0] == pd.Timestamp(
        "2023-11-07T05:40:00Z"
    )


@pytest.mark.parametrize("suffix", [".h5", ".sqlite"])
def test_clip_writes_an_empty_frame_when_the_window_matches_nothing(
    tmp_path: Path, suffix: str
) -> None:
    """Every key in the source is present in the clip, so a consumer's
    `has_frame` answers the same against both."""
    clip_source_file = _clip_source_bundle(tmp_path / f"full_grid{suffix}")
    output_file = tmp_path / f"dense_grid{suffix}"

    result = run_clip_deployment_bundle(
        _clip_command(
            clip_source_file,
            output_file,
            start="2023-11-07T12:00:00Z",
            end="2023-11-07T13:00:00Z",
        )
    )

    key = "telemetry/raw/depth/PAROSCI/messages"
    assert key in result.empty_keys
    with open_deployment_bundle_reader(output_file) as reader:
        assert reader.has_frame(key)
        frame = reader.read_frame(key)

    assert frame.empty
    assert list(frame.columns) == ["timestamp", "depth"]


def test_clip_leaves_the_source_bundle_unchanged(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """A clip cannot damage the bundle it reads."""
    before = clip_source_file.read_bytes()

    run_clip_deployment_bundle(
        _clip_command(clip_source_file, tmp_path / "dense_grid.sqlite")
    )

    assert clip_source_file.read_bytes() == before


def test_clip_repeats_the_row_on_a_shared_bound(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """Adjacent closed windows both keep the row on the bound they share, so
    cutting a source into touching windows does not partition it."""
    key = "telemetry/raw/depth/PAROSCI/messages"
    first = tmp_path / "first.sqlite"
    second = tmp_path / "second.sqlite"

    run_clip_deployment_bundle(
        _clip_command(
            clip_source_file,
            first,
            start="2023-11-07T05:00:00Z",
            end="2023-11-07T05:20:00Z",
        )
    )
    run_clip_deployment_bundle(
        _clip_command(
            clip_source_file,
            second,
            start="2023-11-07T05:20:00Z",
            end="2023-11-07T06:00:00Z",
            label_suffix="dense02",
        )
    )

    with open_deployment_bundle_reader(first) as reader:
        first_depths = reader.read_frame(key)["depth"].tolist()
    with open_deployment_bundle_reader(second) as reader:
        second_depths = reader.read_frame(key)["depth"].tolist()

    assert first_depths == [1.0, 2.0, 3.0]
    assert second_depths == [3.0, 4.0, 5.0]
    assert set(first_depths) & set(second_depths) == {3.0}


def test_clip_rejects_a_start_not_before_its_end(
    clip_source_file: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="must be before its end"):
        run_clip_deployment_bundle(
            _clip_command(
                clip_source_file,
                tmp_path / "dense_grid.sqlite",
                start="2023-11-07T05:40:00Z",
                end="2023-11-07T05:10:00Z",
            )
        )


def test_clip_rejects_an_empty_label_suffix(
    clip_source_file: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="label suffix is empty"):
        run_clip_deployment_bundle(
            _clip_command(
                clip_source_file,
                tmp_path / "dense_grid.sqlite",
                label_suffix="",
            )
        )


def test_clip_rejects_an_existing_output_without_overwrite(
    clip_source_file: Path, tmp_path: Path
) -> None:
    output_file = tmp_path / "dense_grid.sqlite"
    output_file.write_bytes(b"")

    with pytest.raises(ValueError, match="already exists"):
        run_clip_deployment_bundle(_clip_command(clip_source_file, output_file))


def test_clip_rejects_writing_over_its_input(clip_source_file: Path) -> None:
    with pytest.raises(ValueError, match="is the input bundle"):
        run_clip_deployment_bundle(
            _clip_command(clip_source_file, clip_source_file, overwrite=True)
        )


def test_clip_leaves_no_output_when_it_fails(
    clip_source_file: Path, tmp_path: Path
) -> None:
    """A clip that fails halfway leaves no bundle rather than a partial one."""
    output_file = tmp_path / "dense_grid.sqlite"

    with pytest.raises(ValueError, match="not a datetime column"):
        run_clip_deployment_bundle(
            _clip_command(
                clip_source_file, output_file, datetime_column="depth"
            )
        )

    assert not output_file.exists()
    assert list(tmp_path.glob("*.partial*")) == []


@pytest.mark.parametrize("suffix", [".h5", ".sqlite"])
def test_clip_round_trips_through_both_backends(
    tmp_path: Path, suffix: str
) -> None:
    source_file = _clip_source_bundle(tmp_path / f"full_grid{suffix}")
    output_file = tmp_path / f"dense_grid{suffix}"

    run_clip_deployment_bundle(_clip_command(source_file, output_file))

    with open_deployment_bundle_reader(output_file) as reader:
        frame = reader.read_frame("telemetry/raw/depth/PAROSCI/messages")

    assert frame["depth"].tolist() == [2.0, 3.0, 4.0]


def test_cli_clips_a_deployment_bundle(
    clip_source_file: Path, tmp_path: Path
) -> None:
    output_file = tmp_path / "dense_grid.sqlite"

    result: Result = CliRunner().invoke(
        cli,
        [
            "bundle",
            "clip",
            "--input",
            str(clip_source_file),
            "--output",
            str(output_file),
            "--start",
            "2023-11-07T05:10:00",
            "--end",
            "2023-11-07T05:40:00",
            "--label-suffix",
            "dense01",
            "--no-clip",
            "metocean/*",
        ],
    )

    assert result.exit_code == 0, result.output
    with open_deployment_bundle_reader(output_file) as reader:
        assert len(reader.read_frame("metocean/stormglass/wave_height")) == 2
        assert (
            len(reader.read_frame("telemetry/raw/depth/PAROSCI/messages")) == 3
        )
