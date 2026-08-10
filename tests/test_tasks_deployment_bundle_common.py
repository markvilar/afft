"""Tests for the common deployment bundle tasks."""

from pathlib import Path

import pandas as pd
import pytest

from click.testing import CliRunner, Result

from afft.cli.entrypoint import cli
from afft.deployment import (
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.tasks.deployment_bundle_common import (
    IngestBundleFrameCommand,
    IngestBundleFrameResult,
    read_frame_file,
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
