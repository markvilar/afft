"""Pipeline execution engine and processor registry."""

from typing import Callable

import pandas as pd

from .types import TelemetryPipelineConfig, TelemetryPipelineContext

type TelemetryProcessor = Callable[..., pd.DataFrame]

_REGISTRY: dict[str, TelemetryProcessor] = {}


def register_processor(
    name: str,
) -> Callable[[TelemetryProcessor], TelemetryProcessor]:
    """Decorator to register a processor function under a given name."""

    def decorator(processor: TelemetryProcessor) -> TelemetryProcessor:
        _REGISTRY[name] = processor
        return processor

    return decorator


def get_processor(name: str) -> TelemetryProcessor:
    if name not in _REGISTRY:
        raise KeyError(f"unknown processor: {name!r}")
    return _REGISTRY[name]


def run_pipeline(
    context: TelemetryPipelineContext,
    config: TelemetryPipelineConfig,
) -> TelemetryPipelineContext:
    """Run each processor spec in order, updating the context in place.

    Each processor is called as processor(*dfs, spec.config) where dfs are the
    DataFrames from the context in the order declared in spec.inputs.
    When spec.config is None the processor is called without a config argument,
    relying on its default.
    """
    for spec in config.specs:
        processor: TelemetryProcessor = get_processor(spec.processor)
        dfs: list[pd.DataFrame] = context.extract(spec.inputs)
        if spec.config is None:
            context.set_table(spec.output, processor(*dfs))
        else:
            context.set_table(spec.output, processor(*dfs, spec.config))
    return context
