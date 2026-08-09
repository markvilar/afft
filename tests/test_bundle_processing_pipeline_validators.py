"""Tests for validating a resolved pipeline against a bundle's keys."""

from collections.abc import Mapping

import pandas as pd
import pytest

from pydantic import BaseModel, ConfigDict

from afft.bundle_processing import PipelineStep, validate_pipeline


class _ScaleConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    factor: float = 2.0


def _scale(
    frames: Mapping[str, pd.DataFrame], config: _ScaleConfig
) -> pd.DataFrame:
    """Never called: validation resolves keys without running processors."""
    return frames["df"]


def _step(
    output: str,
    source_key: str = "telemetry/raw/pressure",
) -> PipelineStep:
    return PipelineStep(
        processor_key="scale",
        processor=_scale,
        config=_ScaleConfig(),
        inputs={"df": source_key},
        output=output,
    )


def test_validate_accepts_inputs_the_source_holds() -> None:
    """A step reading a key the input bundle holds validates."""
    validate_pipeline(
        (_step("telemetry/processed/pressure"),),
        {"telemetry/raw/pressure"},
    )


def test_validate_accepts_inputs_an_earlier_step_produces() -> None:
    """A step reading an earlier step's output validates."""
    pipeline = (
        _step("telemetry/processed/once"),
        _step(
            "telemetry/processed/twice", source_key="telemetry/processed/once"
        ),
    )

    validate_pipeline(pipeline, {"telemetry/raw/pressure"})


def test_validate_rejects_an_unreachable_input() -> None:
    """A key neither held nor produced fails before the run starts."""
    pipeline = (_step("out", source_key="telemetry/absent"),)

    with pytest.raises(ValueError, match="step 0"):
        validate_pipeline(pipeline, {"telemetry/raw/pressure"})


def test_validate_rejects_a_forward_reference() -> None:
    """Reading a key a *later* step produces fails: order is significant."""
    pipeline = (
        _step(
            "telemetry/processed/once", source_key="telemetry/processed/twice"
        ),
        _step("telemetry/processed/twice"),
    )

    with pytest.raises(ValueError, match="step 0"):
        validate_pipeline(pipeline, {"telemetry/raw/pressure"})
