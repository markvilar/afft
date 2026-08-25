"""Tests for the deployment bundle datatypes."""

from datetime import datetime

import pytest

from pydantic import ValidationError

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
        deployment_start_datetime=datetime(2010, 10, 3, 5, 44, 52),
    )
    assert identity.deployment_label == (
        "r20101003_054452_alligator_creek_south_02"
    )


def test_deployment_identity_end_defaults_to_none() -> None:
    """A deployment covering its full temporal range records no end."""
    identity: DeploymentIdentity = DeploymentIdentity(
        deployment_label="r20101003_054452_alligator_creek_south_02",
        deployment_start_datetime=datetime(2010, 10, 3, 5, 44, 52),
    )
    assert identity.deployment_end_datetime is None


def test_deployment_identity_accepts_a_temporal_range() -> None:
    """A clipped deployment records both bounds."""
    identity: DeploymentIdentity = DeploymentIdentity(
        deployment_label="r20101003_054452_alligator_creek_south_02_dense01",
        deployment_start_datetime=datetime(2010, 10, 3, 5, 44, 52),
        deployment_end_datetime=datetime(2010, 10, 3, 6, 14, 52),
    )
    assert identity.deployment_end_datetime == datetime(2010, 10, 3, 6, 14, 52)


@pytest.mark.parametrize(
    "end",
    [
        datetime(2010, 10, 3, 5, 44, 52),
        datetime(2010, 10, 3, 4, 0, 0),
    ],
    ids=["equal-to-start", "before-start"],
)
def test_deployment_identity_rejects_an_end_not_after_its_start(
    end: datetime,
) -> None:
    """An end at or before the start is not a temporal range."""
    with pytest.raises(ValidationError, match="must be after its start"):
        DeploymentIdentity(
            deployment_label="r20101003_054452_alligator_creek_south_02",
            deployment_start_datetime=datetime(2010, 10, 3, 5, 44, 52),
            deployment_end_datetime=end,
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
