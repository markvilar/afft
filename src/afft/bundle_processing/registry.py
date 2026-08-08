"""Name-to-processor registry used to resolve configured pipeline steps."""

from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel

from .types import PipelineProcessor


@dataclass(slots=True, frozen=True)
class RegisteredProcessor:
    """
    A processor and the config type its `config` table is parsed into.

    Attributes
    ----------
    processor: The wrapper conforming to `PipelineProcessor`.
    config_type: Model the step's raw `config` table is constructed as.
    """

    processor: PipelineProcessor
    config_type: type[BaseModel]


class PipelineProcessorRegistry:
    """Name-to-processor mapping for pipeline construction."""

    def __init__(self) -> None:
        self._processors: dict[str, RegisteredProcessor] = {}

    def register(
        self, name: str, config_type: type[BaseModel]
    ) -> Callable[[PipelineProcessor], PipelineProcessor]:
        """
        Return a decorator registering a processor under `name`.

        The decorated function is returned unchanged, so it stays directly
        callable and testable without going through the registry.

        Arguments
        ---------
        name: Name the processor is configured by.
        config_type: Model the step's raw `config` table is constructed as.

        Returns
        -------
        A decorator that registers its argument and returns it unchanged.

        Raises
        ------
        ValueError: If `name` is already registered.
        """

        def decorator(processor: PipelineProcessor) -> PipelineProcessor:
            if name in self._processors:
                raise ValueError(f"processor already registered: {name!r}")
            self._processors[name] = RegisteredProcessor(
                processor=processor,
                config_type=config_type,
            )
            return processor

        return decorator

    def get(self, name: str) -> RegisteredProcessor:
        """
        Look up a registered processor.

        Arguments
        ---------
        name: Name the processor was registered under.

        Returns
        -------
        The registered processor and its config type.

        Raises
        ------
        KeyError: If no processor is registered under `name`.
        """
        if name not in self._processors:
            raise KeyError(name)
        return self._processors[name]

    def names(self) -> list[str]:
        """List every registered processor name, sorted."""
        return sorted(self._processors)


_REGISTRY: PipelineProcessorRegistry = PipelineProcessorRegistry()
register_processor = _REGISTRY.register


def default_registry() -> PipelineProcessorRegistry:
    """Return the process-wide registry the decorators populate."""
    return _REGISTRY
