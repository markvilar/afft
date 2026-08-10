"""Package for bundle-in/bundle-out processing pipelines."""

from .pipeline_types import (
    Pipeline as Pipeline,
    PipelineConfig as PipelineConfig,
    PipelineProcessor as PipelineProcessor,
    PipelineStep as PipelineStep,
    PipelineStepConfig as PipelineStepConfig,
)
from .processor_registry import (
    PipelineProcessorRegistry as PipelineProcessorRegistry,
    RegisteredProcessor as RegisteredProcessor,
    default_registry as default_registry,
    register_processor as register_processor,
)
from .pipeline_builders import build_pipeline as build_pipeline
from .pipeline_validators import validate_pipeline as validate_pipeline
from .pipeline_runners import (
    PipelineStepError as PipelineStepError,
    run_pipeline as run_pipeline,
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
