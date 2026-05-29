"""TOML pipeline config loader for the process telemetry task."""

from pathlib import Path
from typing import Any

from afft.io.config_io import read_config
from afft.sensors.acfr_vision import PairStereoImagesConfig
from afft.sensors.dvl_teledyne import DvlUncertaintyConfig
from afft.sensors.pressure_parosci import PressureUncertaintyConfig
from afft.sensors.usbl_linkquest import (
    UsblResolvePositionConfig,
    UsblUncertaintyConfig,
)
from afft.telemetry_processing import (
    TelemetryPipelineConfig,
    TelemetryProcessorSpec,
)

_CONFIG_CLASSES: dict[str, type] = {
    "pair_stereo_images": PairStereoImagesConfig,
    "estimate_dvl_uncertainty": DvlUncertaintyConfig,
    "estimate_pressure_uncertainty": PressureUncertaintyConfig,
    "resolve_usbl_position": UsblResolvePositionConfig,
    "estimate_usbl_uncertainty": UsblUncertaintyConfig,
}


def _build_processor_config(name: str, params: dict[str, Any]) -> Any:
    config_cls = _CONFIG_CLASSES.get(name)
    if config_cls is None:
        return None
    return config_cls(**params)


def load_pipeline_config(path: Path) -> TelemetryPipelineConfig:
    """Load a TOML pipeline config file and return a TelemetryPipelineConfig.

    Each [[telemetry_processing_pipeline]] entry must have processor, inputs,
    and output fields. An optional inline config table supplies parameters
    for the processor's config dataclass; omitting it uses the processor's
    defaults.

    Example entry:
        [[telemetry_processing_pipeline]]
        processor = "pair_stereo_images"
        inputs    = ["image_capture"]
        output    = "image_capture"
        config    = {left_suffix = "LC16", right_suffix = "RM16"}
    """
    raw = read_config(path)
    specs = []

    for entry in raw.get("telemetry_processing_pipeline", []):
        name = entry["processor"]
        inputs = tuple(entry["inputs"])
        output = entry["output"]
        params = entry.get("config", {})
        processor_config = _build_processor_config(name, params)
        specs.append(
            TelemetryProcessorSpec(
                processor=name,
                inputs=inputs,
                output=output,
                config=processor_config,
            )
        )

    return TelemetryPipelineConfig(specs=tuple(specs))
