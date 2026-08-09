"""Resolution of a configured pipeline into runnable steps."""

from pydantic import ValidationError

from .pipeline_types import Pipeline, PipelineConfig, PipelineStep
from .processor_registry import PipelineProcessorRegistry, default_registry


def build_pipeline(
    config: PipelineConfig,
    registry: PipelineProcessorRegistry | None = None,
) -> Pipeline:
    """
    Resolve each configured step into a runnable pipeline.

    Arguments
    ---------
    config: The pipeline as declared in the config file.
    registry: Registry to resolve processor names against. Defaults to the
        process-wide registry the decorators populate.

    Returns
    -------
    The resolved steps, in declaration order.

    Raises
    ------
    ValueError: If a step names an unknown processor, or its `config` table
        is not valid for that processor.
    """
    registry = registry if registry is not None else default_registry()

    steps: list[PipelineStep] = []
    for index, step_config in enumerate(config.steps):
        try:
            registered = registry.get(step_config.processor)
        except KeyError:
            raise ValueError(
                f"step {index} names unknown processor "
                f"{step_config.processor!r}; "
                f"registered processors are {registry.names()}"
            ) from None

        try:
            step_config_model = registered.config_type(**step_config.config)
        except ValidationError as error:
            raise ValueError(
                f"step {index} ({step_config.processor}) has an invalid "
                f"config: {error}"
            ) from error

        steps.append(
            PipelineStep(
                processor_key=step_config.processor,
                processor=registered.processor,
                config=step_config_model,
                inputs=dict(step_config.inputs),
                output=step_config.output,
            )
        )

    return tuple(steps)
