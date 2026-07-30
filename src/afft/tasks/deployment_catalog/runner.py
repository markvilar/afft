"""Runner for the scaffold catalog task."""

from afft.deployment import (
    DeploymentCatalog,
    DeploymentDescriptor,
    read_deployment_descriptors,
    write_deployment_catalog,
)
from afft.utils.log import logger

from .builders import (
    build_deployment_platforms,
    build_deployment_vessels,
    build_platform_profile_stubs,
    build_sensor_stubs,
    build_vessel_profile_stubs,
    map_platform_profile_keys,
    map_vessel_profile_keys,
)
from .types import (
    ScaffoldCatalogCommand,
    ScaffoldCatalogDiagnostics,
    ScaffoldCatalogResult,
)


def scaffold_catalog(
    descriptors: list[DeploymentDescriptor],
    diagnostics: ScaffoldCatalogDiagnostics,
) -> DeploymentCatalog:
    """
    Scaffold a catalog skeleton from a set of deployment descriptors.

    Curated content — vessel names, vendor and product, and every mounting pose
    — is not derivable from a deployment and is left empty for the curator. What
    the skeleton does carry is completeness: every deployment is assigned a
    profile, so none is silently missed.

    Arguments
    ---------
    descriptors: Deployment descriptors to scaffold from.
    diagnostics: Accumulator for non-fatal issues.

    Returns
    -------
    The scaffolded catalog.
    """
    platform_keys: dict[str, str] = map_platform_profile_keys(descriptors)
    vessel_keys: dict[str, str] = map_vessel_profile_keys(
        descriptors, diagnostics
    )

    return DeploymentCatalog(
        sensors=build_sensor_stubs(descriptors),
        platform_profiles=build_platform_profile_stubs(
            descriptors, platform_keys, diagnostics
        ),
        vessel_profiles=build_vessel_profile_stubs(vessel_keys),
        deployment_platforms=build_deployment_platforms(
            descriptors, platform_keys
        ),
        deployment_vessels=build_deployment_vessels(descriptors, vessel_keys),
    )


def run_scaffold_catalog(
    command: ScaffoldCatalogCommand,
) -> ScaffoldCatalogResult:
    """
    Scaffold a deployment catalog from a descriptors file and write it to TOML.

    Arguments
    ---------
    command: Task command.

    Returns
    -------
    The written catalog and the run's diagnostics.
    """
    if not command.input_file.exists():
        raise FileNotFoundError(
            f"input file does not exist: {command.input_file}"
        )
    if not command.output_file.parent.exists():
        raise FileNotFoundError(
            f"output directory does not exist: {command.output_file.parent}"
        )

    logger.info("-------------------------------------")
    logger.info("Scaffold Deployment Catalog")
    logger.info(f"  input file:  {command.input_file}")
    logger.info(f"  output file: {command.output_file}")
    logger.info(f"  verbose:     {command.verbose}")
    logger.info("-------------------------------------")

    descriptors: list[DeploymentDescriptor] = read_deployment_descriptors(
        command.input_file
    )
    if not descriptors:
        raise ValueError(f"no deployments in {command.input_file}")

    logger.info(f"scaffolding from {len(descriptors)} deployment(s)")

    diagnostics = ScaffoldCatalogDiagnostics()
    catalog: DeploymentCatalog = scaffold_catalog(descriptors, diagnostics)

    write_deployment_catalog(command.output_file, catalog)
    logger.info(
        f"wrote {len(catalog.platform_profiles)} platform profile(s), "
        f"{len(catalog.vessel_profiles)} vessel profile(s), and "
        f"{len(catalog.sensors)} sensor stub(s) to {command.output_file}"
    )

    if command.verbose:
        for warning in diagnostics.warnings:
            logger.warning(f"{warning.deployment_label}: {warning.message}")

    return ScaffoldCatalogResult(catalog=catalog, diagnostics=diagnostics)
