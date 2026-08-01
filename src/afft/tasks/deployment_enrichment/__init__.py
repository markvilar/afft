"""Task for enriching deployment descriptors from a curated catalog."""

from .runner import (
    enrich_descriptors as enrich_descriptors,
    run_enrich_descriptor as run_enrich_descriptor,
)
from .types import (
    EnrichDescriptorCommand as EnrichDescriptorCommand,
    EnrichDescriptorDiagnostics as EnrichDescriptorDiagnostics,
    EnrichDescriptorResult as EnrichDescriptorResult,
    EnrichmentWarning as EnrichmentWarning,
)

__all__ = []
