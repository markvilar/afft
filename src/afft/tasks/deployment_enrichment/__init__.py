"""Tasks for enriching deployment descriptors from a catalog or Squidle+."""

from .catalog import (
    enrich_descriptors_from_catalog as enrich_descriptors_from_catalog,
    run_enrich_descriptors_from_catalog as run_enrich_descriptors_from_catalog,
)
from .squidle import (
    match_squidle_deployments as match_squidle_deployments,
    resolve_squidle_deployment as resolve_squidle_deployment,
    resolve_squidle_identity as resolve_squidle_identity,
    run_enrich_descriptors_from_squidle as run_enrich_descriptors_from_squidle,
)
from .types import (
    DeploymentMatchPolicy as DeploymentMatchPolicy,
    EnrichCatalogCommand as EnrichCatalogCommand,
    EnrichCatalogDiagnostics as EnrichCatalogDiagnostics,
    EnrichCatalogResult as EnrichCatalogResult,
    EnrichmentWarning as EnrichmentWarning,
    EnrichSquidleCommand as EnrichSquidleCommand,
    EnrichSquidleDiagnostics as EnrichSquidleDiagnostics,
    EnrichSquidleResult as EnrichSquidleResult,
)

__all__ = []
