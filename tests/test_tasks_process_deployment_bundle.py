"""Tests for the process deployment bundle task."""

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from afft.bundle_processing import PipelineStepError
from afft.deployment import (
    open_deployment_bundle,
    open_deployment_bundle_reader,
)
from afft.tasks.process_deployment_bundle import (
    ProcessDeploymentBundleCommand,
    ProcessDeploymentBundleResult,
    run_process_deployment_bundle,
)
from afft.utils.log import logger

RENAME_STEP: str = """
[[afft.tasks.process_deployment_bundle.pipeline.steps]]
processor = "rename_columns"
output = "telemetry/processed/pressure/messages"
inputs.df = "telemetry/raw/pressure/messages"
config.columns.value = "pressure"
"""

MISSING_INPUT_STEP: str = """
[[afft.tasks.process_deployment_bundle.pipeline.steps]]
processor = "rename_columns"
output = "telemetry/processed/pressure/messages"
inputs.df = "telemetry/raw/absent/messages"
config.columns.value = "pressure"
"""

MISSING_COLUMN_STEP: str = """
[[afft.tasks.process_deployment_bundle.pipeline.steps]]
processor = "rename_columns"
output = "telemetry/processed/pressure/messages"
inputs.df = "telemetry/raw/pressure/messages"
config.columns.absent = "pressure"
"""


def _config_file(directory: Path, body: str) -> Path:
    config_file: Path = directory / "task.toml"
    config_file.write_text(body)
    return config_file


def _input_bundle(path: Path) -> Path:
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "telemetry/raw/pressure/messages",
            pd.DataFrame({"value": [1.0, 2.0]}),
        )
    return path


def _command(
    tmp_path: Path, body: str, **overrides: Any
) -> ProcessDeploymentBundleCommand:
    arguments: dict[str, Any] = {
        "input_file": _input_bundle(tmp_path / "in.h5"),
        "config_file": _config_file(tmp_path, body),
        "output_file": tmp_path / "out.h5",
    }
    arguments.update(overrides)
    return ProcessDeploymentBundleCommand(**arguments)


def _staged(output_file: Path) -> Path:
    return output_file.with_suffix(".partial" + output_file.suffix)


def test_writes_the_processed_bundle(tmp_path: Path) -> None:
    """A successful run leaves the processed bundle at the output path."""
    command = _command(tmp_path, RENAME_STEP)

    result = run_process_deployment_bundle(command)

    assert isinstance(result, ProcessDeploymentBundleResult)
    with open_deployment_bundle_reader(tmp_path / "out.h5") as reader:
        frame = reader.read_frame("telemetry/processed/pressure/messages")
    assert frame["pressure"].tolist() == [1.0, 2.0]


def test_reports_the_keys_the_steps_wrote(tmp_path: Path) -> None:
    """The result names each step's output key, in run order."""
    command = _command(tmp_path, RENAME_STEP)

    result = run_process_deployment_bundle(command)

    assert result.output_keys == ("telemetry/processed/pressure/messages",)


def test_a_successful_run_leaves_no_staged_file(tmp_path: Path) -> None:
    """The staged file is moved into place, not left beside the output."""
    command = _command(tmp_path, RENAME_STEP)

    run_process_deployment_bundle(command)

    assert not _staged(tmp_path / "out.h5").exists()


def test_a_failed_step_leaves_neither_output_nor_staged_file(
    tmp_path: Path,
) -> None:
    """A run that dies mid-pipeline leaves nothing behind."""
    command = _command(tmp_path, MISSING_COLUMN_STEP)

    with pytest.raises(PipelineStepError):
        run_process_deployment_bundle(command)

    assert not (tmp_path / "out.h5").exists()
    assert not _staged(tmp_path / "out.h5").exists()


def test_a_failed_run_leaves_the_input_untouched(tmp_path: Path) -> None:
    """The input bundle survives a failed run unchanged."""
    command = _command(tmp_path, MISSING_COLUMN_STEP)

    with pytest.raises(PipelineStepError):
        run_process_deployment_bundle(command)

    with open_deployment_bundle_reader(tmp_path / "in.h5") as reader:
        assert reader.read_frame("telemetry/raw/pressure/messages")[
            "value"
        ].tolist() == [1.0, 2.0]


def test_an_unreachable_input_key_fails_before_the_run(
    tmp_path: Path,
) -> None:
    """`validate_pipeline` rejects the pipeline before anything is written."""
    command = _command(tmp_path, MISSING_INPUT_STEP)

    with pytest.raises(ValueError, match="step 0"):
        run_process_deployment_bundle(command)

    assert not (tmp_path / "out.h5").exists()
    assert not _staged(tmp_path / "out.h5").exists()


def test_rejects_an_output_that_resolves_to_the_input(
    tmp_path: Path,
) -> None:
    """A differently spelled path naming the input is still the input."""
    command = _command(
        tmp_path,
        RENAME_STEP,
        output_file=tmp_path / "sub" / ".." / "in.h5",
    )
    (tmp_path / "sub").mkdir()

    with pytest.raises(ValueError, match="output file is the input file"):
        run_process_deployment_bundle(command)


def test_rejects_an_existing_output_without_overwrite(
    tmp_path: Path,
) -> None:
    """An existing output is an error unless `overwrite` is set."""
    (tmp_path / "out.h5").write_text("existing")
    command = _command(tmp_path, RENAME_STEP)

    with pytest.raises(ValueError, match="already exists"):
        run_process_deployment_bundle(command)

    assert (tmp_path / "out.h5").read_text() == "existing"


def test_overwrite_replaces_an_existing_output(tmp_path: Path) -> None:
    """With `overwrite`, the existing output is replaced by the run's."""
    (tmp_path / "out.h5").write_text("existing")
    command = _command(tmp_path, RENAME_STEP, overwrite=True)

    run_process_deployment_bundle(command)

    with open_deployment_bundle_reader(tmp_path / "out.h5") as reader:
        assert reader.has_frame("telemetry/processed/pressure/messages")


def test_verbose_logs_each_step_output_key(tmp_path: Path) -> None:
    """`verbose` reports each step's output key as it is written."""
    command = _command(tmp_path, RENAME_STEP, verbose=True)

    messages: list[str] = []
    handler_id: int = logger.add(messages.append, level="INFO")
    try:
        run_process_deployment_bundle(command)
    finally:
        logger.remove(handler_id)

    assert any(
        "telemetry/processed/pressure/messages" in message
        and "wrote" in message
        for message in messages
    )
