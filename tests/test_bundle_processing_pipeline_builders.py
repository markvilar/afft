"""Tests for resolving a configured pipeline into runnable steps."""

import pytest

from afft.bundle_processing import (
    PipelineConfig,
    PipelineStepConfig,
    build_pipeline,
)
from afft.sensors.pressure_parosci import PressureUncertaintyConfig


def _step_config(**overrides: object) -> PipelineStepConfig:
    fields: dict[str, object] = {
        "processor": "estimate_pressure_uncertainty",
        "output": "telemetry/processed/pressure",
        "inputs": {"df": "telemetry/raw/pressure"},
        "config": {"base_uncertainty": 0.1},
    }
    fields.update(overrides)
    return PipelineStepConfig(**fields)


def test_resolves_a_step_into_a_runnable_one() -> None:
    """A configured step comes back with its processor and typed config."""
    pipeline = build_pipeline(PipelineConfig(steps=[_step_config()]))

    (step,) = pipeline
    assert step.processor_key == "estimate_pressure_uncertainty"
    assert isinstance(step.config, PressureUncertaintyConfig)
    assert step.config.base_uncertainty == 0.1
    assert step.inputs == {"df": "telemetry/raw/pressure"}
    assert step.output == "telemetry/processed/pressure"


def test_preserves_declaration_order() -> None:
    """Steps come back in the order they were declared."""
    config = PipelineConfig(
        steps=[
            _step_config(output="first"),
            _step_config(output="second"),
        ]
    )

    pipeline = build_pipeline(config)

    assert [step.output for step in pipeline] == ["first", "second"]


def test_applies_processor_config_defaults() -> None:
    """An omitted config field takes the processor config's own default."""
    pipeline = build_pipeline(PipelineConfig(steps=[_step_config(config={})]))

    (step,) = pipeline
    assert isinstance(step.config, PressureUncertaintyConfig)
    assert step.config.base_uncertainty == 0.005


def test_an_unknown_processor_is_a_load_time_error() -> None:
    """A misspelled processor name fails at build, naming what is available."""
    config = PipelineConfig(steps=[_step_config(processor="no_such_thing")])

    with pytest.raises(ValueError, match="unknown processor"):
        build_pipeline(config)


def test_an_unknown_config_field_is_a_load_time_error() -> None:
    """`extra="forbid"` turns a stray config key into a build failure."""
    config = PipelineConfig(
        steps=[_step_config(config={"base_uncertanty": 0.1})]
    )

    with pytest.raises(ValueError, match="invalid config"):
        build_pipeline(config)


def test_a_later_step_failing_reports_its_index() -> None:
    """The error names which step is at fault, not just that one is."""
    config = PipelineConfig(
        steps=[_step_config(), _step_config(processor="no_such_thing")]
    )

    with pytest.raises(ValueError, match="step 1"):
        build_pipeline(config)


def test_an_empty_pipeline_builds() -> None:
    """No steps is a valid pipeline, not an error."""
    assert build_pipeline(PipelineConfig()) == ()
