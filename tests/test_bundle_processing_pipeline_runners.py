"""Tests for running a resolved pipeline against a deployment bundle."""

from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import pytest

from pydantic import BaseModel, ConfigDict

from afft.bundle_processing import (
    Pipeline,
    PipelineStep,
    PipelineStepError,
    run_pipeline,
)
from afft.deployment import (
    open_deployment_bundle,
    open_deployment_bundle_reader,
)


class _ScaleConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    factor: float = 2.0


def _scale(
    frames: Mapping[str, pd.DataFrame], config: _ScaleConfig
) -> pd.DataFrame:
    frame = frames["df"].copy()
    frame["value"] = frame["value"] * config.factor
    return frame


def _fail(
    frames: Mapping[str, pd.DataFrame], config: _ScaleConfig
) -> pd.DataFrame:
    raise RuntimeError("processor exploded")


def _step(
    output: str,
    source_key: str = "telemetry/raw/pressure",
    processor_key: str = "scale",
    factor: float = 2.0,
) -> PipelineStep:
    return PipelineStep(
        processor_key=processor_key,
        processor=_scale if processor_key == "scale" else _fail,
        config=_ScaleConfig(factor=factor),
        inputs={"df": source_key},
        output=output,
    )


def _source_bundle(path: Path) -> None:
    with open_deployment_bundle(path) as bundle:
        bundle.write_frame(
            "telemetry/raw/pressure",
            pd.DataFrame({"value": [1.0, 2.0]}),
        )
        bundle.write_frame(
            "deployment/identity",
            pd.DataFrame({"label": ["dive-01"]}),
        )


def _run(source: Path, target: Path, pipeline: Pipeline) -> None:
    with open_deployment_bundle_reader(source) as reader:
        with open_deployment_bundle(target) as bundle:
            run_pipeline(pipeline, reader, bundle)


def test_seeds_every_input_key_into_the_target(tmp_path: Path) -> None:
    """The output holds every key the input held, even with no steps."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    _run(source, target, ())

    with open_deployment_bundle_reader(target) as reader:
        assert sorted(reader.list_frames()) == [
            "deployment/identity",
            "telemetry/raw/pressure",
        ]


def test_writes_a_processed_frame_alongside_the_seeded_ones(
    tmp_path: Path,
) -> None:
    """A step's output is added without disturbing the inherited keys."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    _run(source, target, (_step("telemetry/processed/pressure"),))

    with open_deployment_bundle_reader(target) as reader:
        assert reader.has_frame("telemetry/raw/pressure")
        assert reader.read_frame("telemetry/processed/pressure")[
            "value"
        ].tolist() == [2.0, 4.0]


def test_a_step_reads_an_earlier_steps_output(tmp_path: Path) -> None:
    """Steps chain: a later step consumes what an earlier one produced."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (
        _step("telemetry/processed/once"),
        _step(
            "telemetry/processed/twice", source_key="telemetry/processed/once"
        ),
    )
    _run(source, target, pipeline)

    with open_deployment_bundle_reader(target) as reader:
        assert reader.read_frame("telemetry/processed/twice")[
            "value"
        ].tolist() == [4.0, 8.0]


def test_a_step_may_overwrite_an_inherited_key(tmp_path: Path) -> None:
    """Overwriting a key the input supplied is supported, not an error."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    _run(source, target, (_step("telemetry/raw/pressure"),))

    with open_deployment_bundle_reader(target) as reader:
        assert reader.read_frame("telemetry/raw/pressure")[
            "value"
        ].tolist() == [2.0, 4.0]


def test_a_step_reads_an_earlier_steps_overwrite(tmp_path: Path) -> None:
    """A later step sees the overwritten value, not the original."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (
        _step("telemetry/raw/pressure"),
        _step("telemetry/processed/pressure"),
    )
    _run(source, target, pipeline)

    with open_deployment_bundle_reader(target) as reader:
        assert reader.read_frame("telemetry/processed/pressure")[
            "value"
        ].tolist() == [4.0, 8.0]


def test_the_source_bundle_is_left_untouched(tmp_path: Path) -> None:
    """A run that overwrites a key changes the target only."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    _run(source, target, (_step("telemetry/raw/pressure"),))

    with open_deployment_bundle_reader(source) as reader:
        assert reader.read_frame("telemetry/raw/pressure")[
            "value"
        ].tolist() == [1.0, 2.0]


def test_a_failing_step_raises_naming_the_step(tmp_path: Path) -> None:
    """The wrapped error names the step index and processor."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (
        _step("telemetry/processed/first"),
        _step("telemetry/processed/second", processor_key="boom"),
    )

    with pytest.raises(PipelineStepError, match="step 1 .boom"):
        _run(source, target, pipeline)


def test_a_failing_step_chains_the_original_error(tmp_path: Path) -> None:
    """The original exception survives as the cause."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (_step("telemetry/processed/x", processor_key="boom"),)

    with pytest.raises(PipelineStepError) as excinfo:
        _run(source, target, pipeline)

    assert isinstance(excinfo.value.__cause__, RuntimeError)
    assert "processor exploded" in str(excinfo.value.__cause__)


def test_a_missing_input_key_fails_as_that_step(tmp_path: Path) -> None:
    """A step naming an absent bundle key fails as that step, not opaquely."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (_step("telemetry/processed/x", source_key="telemetry/absent"),)

    with pytest.raises(PipelineStepError, match="step 0"):
        _run(source, target, pipeline)


def test_a_run_stops_at_the_first_failure(tmp_path: Path) -> None:
    """Fail-fast: no step after a failing one runs."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    pipeline = (
        _step("telemetry/processed/first", processor_key="boom"),
        _step("telemetry/processed/second"),
    )

    with pytest.raises(PipelineStepError):
        _run(source, target, pipeline)

    with open_deployment_bundle_reader(target) as reader:
        assert not reader.has_frame("telemetry/processed/second")


def test_an_optional_step_is_skipped_when_an_input_is_absent(
    tmp_path: Path,
) -> None:
    """A step whose sensor is not on the deployment is skipped, not fatal."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    step = PipelineStep(
        processor_key="scale",
        processor=_scale,
        config=_ScaleConfig(),
        inputs={"df": "telemetry/raw/usbl"},
        output="telemetry/processed/usbl",
        optional=True,
    )

    _run(source, target, (step,))

    with open_deployment_bundle_reader(target) as reader:
        assert not reader.has_frame("telemetry/processed/usbl")


def test_a_required_step_still_fails_when_an_input_is_absent(
    tmp_path: Path,
) -> None:
    """Optionality is opt-in: a missing input is otherwise fatal."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    with pytest.raises(PipelineStepError):
        _run(source, target, (_step("out", source_key="telemetry/raw/usbl"),))


def test_an_optional_step_runs_when_its_inputs_are_present(
    tmp_path: Path,
) -> None:
    """Optional does not mean skipped -- present inputs run normally."""
    source, target = tmp_path / "in.gpkg", tmp_path / "out.gpkg"
    _source_bundle(source)

    step = PipelineStep(
        processor_key="scale",
        processor=_scale,
        config=_ScaleConfig(factor=3.0),
        inputs={"df": "telemetry/raw/pressure"},
        output="telemetry/processed/pressure",
        optional=True,
    )

    _run(source, target, (step,))

    with open_deployment_bundle_reader(target) as reader:
        frame = reader.read_frame("telemetry/processed/pressure")
        assert frame["value"].tolist() == [3.0, 6.0]
