"""Data types describing a deployment bundle, as distinct from the deployment itself."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeploymentIdentity(BaseModel):
    """
    Core identity of a deployment, stored as the single row of
    ``deployment/identity``.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_datetime: Deployment datetime.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_datetime: datetime


class DeploymentBundleHeader(BaseModel):
    """
    File-level facts about a deployment bundle, stored as the single row of
    the root ``bundle`` table.

    Attributes
    ----------
    schema_version: Layout version the bundle was written against.
    created_datetime: When the bundle file was created.
    builder_version: Version of the builder that produced the bundle.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: str
    created_datetime: datetime
    builder_version: str


class DeploymentProvenance(BaseModel):
    """
    Facts about how a bundle's deployment description was derived, stored as
    the single row of ``deployment/provenance``.

    Fields beyond ``deployment_key`` are unsettled — descriptor hash, catalog
    version, and enrichment version are all candidates but not yet decided
    and are expected to be added later.

    Attributes
    ----------
    deployment_key: Identifier of the deployment the bundle was built from.
    """

    model_config = ConfigDict(frozen=True)

    deployment_key: str


class ProcessedProvenance(BaseModel):
    """
    Facts about how one processed telemetry table was produced, stored
    alongside it at
    ``telemetry/processed/<sensor_key>/<message_topic>/provenance``.

    Fields beyond ``run_datetime`` are unsettled — input paths, processor
    versions, and pipeline config are all candidates but not yet decided and
    are expected to be added later.

    Attributes
    ----------
    run_datetime: When the processing step ran.
    """

    model_config = ConfigDict(frozen=True)

    run_datetime: datetime
