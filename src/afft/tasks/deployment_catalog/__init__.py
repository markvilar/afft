"""Task for scaffolding a curated deployment catalog from descriptors."""

from .builders import (
    build_deployment_platforms as build_deployment_platforms,
    build_deployment_vessels as build_deployment_vessels,
    build_platform_profile_stubs as build_platform_profile_stubs,
    build_sensor_stubs as build_sensor_stubs,
    build_vessel_profile_stubs as build_vessel_profile_stubs,
    map_platform_profile_keys as map_platform_profile_keys,
    map_vessel_profile_keys as map_vessel_profile_keys,
)
from .runner import (
    run_scaffold_catalog as run_scaffold_catalog,
    scaffold_catalog as scaffold_catalog,
)
from .summary_runner import (
    log_summary as log_summary,
    run_summarize_catalog as run_summarize_catalog,
)
from .summary_types import (
    SummarizeCatalogCommand as SummarizeCatalogCommand,
    SummarizeCatalogResult as SummarizeCatalogResult,
)
from .types import (
    CatalogWarning as CatalogWarning,
    ScaffoldCatalogCommand as ScaffoldCatalogCommand,
    ScaffoldCatalogDiagnostics as ScaffoldCatalogDiagnostics,
    ScaffoldCatalogResult as ScaffoldCatalogResult,
)

__all__ = []
