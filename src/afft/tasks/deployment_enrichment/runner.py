"""Runner for the enrich descriptor task."""

from afft.deployment import (
    DeploymentCatalog,
    DeploymentCatalogIndex,
    DeploymentDescriptor,
    DeploymentEnrichment,
    EnrichmentSection,
    enrich_descriptor,
    read_deployment_catalog,
    read_deployment_descriptors,
    write_deployment_descriptors,
)
from afft.utils.log import logger

from .types import (
    EnrichDescriptorCommand,
    EnrichDescriptorDiagnostics,
    EnrichDescriptorResult,
)


def enrich_descriptors(
    descriptors: list[DeploymentDescriptor],
    catalog: DeploymentCatalog,
    diagnostics: EnrichDescriptorDiagnostics,
    section: EnrichmentSection = EnrichmentSection.ALL,
) -> list[DeploymentDescriptor]:
    """
    Enrich a set of deployment descriptors from a curated catalog.

    A deployment the catalog assigns no profile is a curation gap rather than
    a failure: it is reported as a warning and keeps its unfilled slots.

    Arguments
    ---------
    descriptors: Deployment descriptors to enrich.
    catalog: The curated catalog to resolve against.
    diagnostics: Accumulator for non-fatal issues.
    section: The descriptor sections to fill.

    Returns
    -------
    The enriched descriptors, in input order.
    """
    index: DeploymentCatalogIndex = DeploymentCatalogIndex.from_catalog(catalog)

    enriched: list[DeploymentDescriptor] = []
    for descriptor in descriptors:
        enrichment: DeploymentEnrichment = enrich_descriptor(
            descriptor, index, section
        )
        if enrichment.platform_matched is False:
            diagnostics.warning(
                descriptor.deployment_label, "no platform profile assigned"
            )
        if enrichment.vessel_matched is False:
            diagnostics.warning(
                descriptor.deployment_label, "no vessel profile assigned"
            )
        enriched.append(enrichment.descriptor)

    return enriched


def run_enrich_descriptor(
    command: EnrichDescriptorCommand,
) -> EnrichDescriptorResult:
    """
    Enrich a descriptors file from a catalog file and write it back to TOML.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The written descriptors and the run's diagnostics.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if not command.catalog_file.exists():
        raise FileNotFoundError(
            f"catalog file does not exist: {command.catalog_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    logger.info("-------------------------------------")
    logger.info("Enrich Deployment Descriptors")
    logger.info(f"  input file:   {command.input_file}")
    logger.info(f"  catalog file: {command.catalog_file}")
    logger.info(f"  output file:  {command.output_file}")
    logger.info(f"  section:      {command.section}")
    logger.info(f"  verbose:      {command.verbose}")
    logger.info("-------------------------------------")

    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        command.input_file
    )
    if not descriptors:
        raise ValueError(f"no deployments in {command.input_file}")

    catalog: DeploymentCatalog = read_deployment_catalog(command.catalog_file)

    logger.info(f"enriching {len(descriptors)} deployment(s)")

    diagnostics = EnrichDescriptorDiagnostics()
    enriched: list[DeploymentDescriptor] = enrich_descriptors(
        descriptors, catalog, diagnostics, command.section
    )

    write_deployment_descriptors(command.output_file, enriched)
    logger.info(
        f"wrote {len(enriched)} enriched deployment(s) to {command.output_file}"
    )

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.deployment_label}: {warning.message}")

    return EnrichDescriptorResult(descriptors=enriched, diagnostics=diagnostics)
