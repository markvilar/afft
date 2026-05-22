"""Pipeline execution engine and processor registry."""

from typing import Callable

import pandas as pd

from .types import PipelineConfig

Processor = Callable[..., pd.DataFrame]

_REGISTRY: dict[str, Processor] = {}


def register(name: str) -> Callable[[Processor], Processor]:
    """Decorator to register a processor function under a given name."""

    def decorator(fn: Processor) -> Processor:
        _REGISTRY[name] = fn
        return fn

    return decorator


def get_processor(name: str) -> Processor:
    if name not in _REGISTRY:
        raise KeyError(f"unknown processor: {name!r}")
    return _REGISTRY[name]


def run_pipeline(
    context: dict[str, pd.DataFrame],
    config: PipelineConfig,
) -> dict[str, pd.DataFrame]:
    """Run each processor spec in order, updating the context in place.

    Each processor is called as processor(*dfs, spec.config) where dfs are the
    DataFrames from the context in the order declared in spec.inputs.
    When spec.config is None the processor is called without a config argument,
    relying on its default.
    """
    for spec in config.specs:
        processor = get_processor(spec.processor)
        dfs = [context[name] for name in spec.inputs]
        if spec.config is None:
            context[spec.output] = processor(*dfs)
        else:
            context[spec.output] = processor(*dfs, spec.config)
    return context
