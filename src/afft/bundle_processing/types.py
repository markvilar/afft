"""Types describing a processing pipeline, its steps, and the config they
are built from."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from pydantic import BaseModel, ConfigDict

type PipelineProcessor = Callable[
    [Mapping[str, pd.DataFrame], Any], pd.DataFrame
]


@dataclass(slots=True, frozen=True)
class PipelineStep:
    """
    A single resolved step, ready to run.

    Attributes
    ----------
    processor_key: Registered name, retained for error messages.
    processor: The resolved processor.
    config: The processor's config, already constructed as its typed model.
    inputs: Maps each processor argument name to the bundle key supplying it.
    output: Bundle key the resulting frame is written to.
    """

    processor_key: str
    processor: PipelineProcessor
    config: BaseModel
    inputs: Mapping[str, str]
    output: str


type Pipeline = tuple[PipelineStep, ...]


class PipelineStepConfig(BaseModel):
    """
    A single step of the processing pipeline, as declared in the config file.

    Attributes
    ----------
    processor: Name of the processor, resolved against the processor registry.
    output: Bundle key the step's resulting frame is written to.
    inputs: Maps each processor argument name to the bundle key supplying it.
    config: Raw config table, constructed as the processor's config type by
        the builder.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    processor: str
    output: str
    inputs: dict[str, str]
    config: dict[str, Any] = {}


class PipelineConfig(BaseModel):
    """
    The processing pipeline as declared in the config file.

    Attributes
    ----------
    steps: The steps to run, in declaration order.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    steps: list[PipelineStepConfig] = []
