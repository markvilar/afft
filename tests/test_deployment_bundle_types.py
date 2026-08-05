"""Tests for the deployment bundle datatypes."""

from datetime import datetime

from afft.deployment import (
    DeploymentBundleHeader,
    DeploymentIdentity,
    DeploymentProvenance,
    ProcessedProvenance,
)


def test_deployment_identity() -> None:
    """Constructs a deployment identity."""
    identity: DeploymentIdentity = DeploymentIdentity(
        deployment_label="r20101003_054452_alligator_creek_south_02",
        deployment_datetime=datetime(2010, 10, 3, 5, 44, 52),
    )
    assert identity.deployment_label == (
        "r20101003_054452_alligator_creek_south_02"
    )


def test_deployment_bundle_header() -> None:
    """Constructs a deployment bundle header."""
    header: DeploymentBundleHeader = DeploymentBundleHeader(
        schema_version="1.0",
        created_datetime=datetime(2026, 8, 5, 12, 0, 0),
        builder_version="0.1.0",
    )
    assert header.schema_version == "1.0"


def test_deployment_provenance() -> None:
    """Constructs a deployment provenance record."""
    provenance: DeploymentProvenance = DeploymentProvenance(
        deployment_key="r20101003_054452_alligator_creek_south_02"
    )
    assert provenance.deployment_key == (
        "r20101003_054452_alligator_creek_south_02"
    )


def test_processed_provenance() -> None:
    """Constructs a processed telemetry provenance record."""
    provenance: ProcessedProvenance = ProcessedProvenance(
        run_datetime=datetime(2026, 8, 5, 12, 0, 0)
    )
    assert provenance.run_datetime == datetime(2026, 8, 5, 12, 0, 0)
