"""Package for bundle-in/bundle-out processing pipelines."""

from .types import (
    Pipeline as Pipeline,
    PipelineConfig as PipelineConfig,
    PipelineProcessor as PipelineProcessor,
    PipelineStep as PipelineStep,
    PipelineStepConfig as PipelineStepConfig,
)
from .registry import (
    PipelineProcessorRegistry as PipelineProcessorRegistry,
    RegisteredProcessor as RegisteredProcessor,
    default_registry as default_registry,
    register_processor as register_processor,
)
from .builders import build_pipeline as build_pipeline
from .runners import (
    PipelineStepError as PipelineStepError,
    run_pipeline as run_pipeline,
    validate_pipeline as validate_pipeline,
)

# Imported for their registration side effects: a processor in an unimported
# module is silently absent from the registry rather than an error.
from . import common_processors as common_processors
from . import sensor_processors as sensor_processors

from .common_processors import (
    DropColumnsConfig as DropColumnsConfig,
    RenameColumnsConfig as RenameColumnsConfig,
    SelectColumnsConfig as SelectColumnsConfig,
)
