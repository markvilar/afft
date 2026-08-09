"""Tests for the pipeline processor registry."""

from collections.abc import Mapping

import pandas as pd
import pytest

from pydantic import BaseModel, ConfigDict

from afft.bundle_processing import (
    PipelineProcessorRegistry,
    default_registry,
)


class _Config(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    factor: float = 1.0


def _processor(
    frames: Mapping[str, pd.DataFrame], config: _Config
) -> pd.DataFrame:
    return frames["df"]


def test_registers_and_resolves_a_processor() -> None:
    """A registered processor is retrievable with its config type."""
    registry = PipelineProcessorRegistry()
    registry.register("scale", config_type=_Config)(_processor)

    registered = registry.get("scale")

    assert registered.processor is _processor
    assert registered.config_type is _Config


def test_returns_the_decorated_function_unchanged() -> None:
    """Decorating leaves the function directly callable."""
    registry = PipelineProcessorRegistry()

    decorated = registry.register("scale", config_type=_Config)(_processor)

    assert decorated is _processor


def test_rejects_a_duplicate_name() -> None:
    """Registering a name twice is an error rather than a silent replace."""
    registry = PipelineProcessorRegistry()
    registry.register("scale", config_type=_Config)(_processor)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("scale", config_type=_Config)(_processor)


def test_raises_key_error_for_an_unknown_name() -> None:
    """An unregistered name raises rather than returning None."""
    registry = PipelineProcessorRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")


def test_lists_names_sorted() -> None:
    """Names come back sorted, independent of registration order."""
    registry = PipelineProcessorRegistry()
    registry.register("zulu", config_type=_Config)(_processor)
    registry.register("alpha", config_type=_Config)(_processor)

    assert registry.names() == ["alpha", "zulu"]


def test_a_local_registry_does_not_leak_into_the_default_one() -> None:
    """Test registries are isolated from the process-wide one."""
    registry = PipelineProcessorRegistry()
    registry.register("only-here", config_type=_Config)(_processor)

    assert "only-here" not in default_registry().names()


def test_default_registry_holds_every_shipped_processor() -> None:
    """Importing the package registers all processors it defines."""
    assert default_registry().names() == [
        "drop_columns",
        "estimate_dvl_uncertainty",
        "estimate_pressure_uncertainty",
        "pair_stereo_images",
        "rename_columns",
        "select_columns",
    ]
