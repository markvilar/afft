"""Data types describing a deployment bundle, as distinct from the deployment itself."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from .common_types import validate_temporal_range


class DeploymentIdentity(BaseModel):
    """
    Core identity of a deployment, stored as the single row of
    ``deployment/identity``.

    Attributes
    ----------
    deployment_label: Deployment identifier in ``<GEOHASH>_<DATETIME>`` format.
    deployment_start_datetime: Start datetime of the deployment.
    deployment_end_datetime: End datetime of the deployment; ``None`` when the
        deployment covers its own full temporal range and no end was recorded.
    """

    model_config = ConfigDict(frozen=True)

    deployment_label: str
    deployment_start_datetime: datetime
    deployment_end_datetime: datetime | None = None

    @model_validator(mode="after")
    def _check_temporal_range(self) -> Self:
        validate_temporal_range(
            self.deployment_start_datetime, self.deployment_end_datetime
        )
        return self


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
    source_bundle: Path to the bundle this one was cut from; ``None`` for a
        bundle built from raw message logs rather than derived from another.
    clip_start_datetime: Start of the window the source bundle was clipped to,
        inclusive; ``None`` when the bundle is not a clip.
    clip_end_datetime: End of the window the source bundle was clipped to,
        inclusive; ``None`` when the bundle is not a clip.
    """

    model_config = ConfigDict(frozen=True)

    deployment_key: str
    source_bundle: str | None = None
    clip_start_datetime: datetime | None = None
    clip_end_datetime: datetime | None = None


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
