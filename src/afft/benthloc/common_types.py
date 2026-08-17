"""Data types and identity resolution shared by both Benthloc ingestion file
builders."""

from pydantic import BaseModel, ConfigDict

from afft.deployment import (
    DeploymentBundleReader,
    DeploymentIdentity,
    PlatformIdentity,
)

_DEPLOYMENT_IDENTITY_KEY: str = "deployment/identity"
_PLATFORM_IDENTITY_KEY: str = "platform/identity"


class ResolvedIdentity(BaseModel):
    """
    Platform and deployment labels to attach to a Benthloc ingestion file.

    Attributes
    ----------
    platform_label: Platform label, e.g. ``"AUV Sirius"``.
    deployment_label: Deployment label, e.g. ``<GEOHASH>_<DATETIME>``.
    """

    model_config = ConfigDict(frozen=True)

    platform_label: str
    deployment_label: str


def resolve_identity(
    reader: DeploymentBundleReader,
    platform_label: str | None,
    deployment_label: str | None,
) -> ResolvedIdentity:
    """
    Resolve the platform and deployment labels for a Benthloc ingestion
    file.

    Each label is taken from its CLI override when given, otherwise read
    from the bundle's own identity.

    Arguments
    ---------
    reader: Bundle to read identity from, for whichever label has no
        override.
    platform_label: CLI override, or ``None`` to read the bundle's
        ``platform/identity``.
    deployment_label: CLI override, or ``None`` to read the bundle's
        ``deployment/identity``.

    Returns
    -------
    The resolved labels.

    Raises
    ------
    KeyError: If a label has no override and the bundle holds no identity
        frame to read it from.
    """
    if platform_label is None:
        platform_identity = PlatformIdentity(
            **reader.read_frame(_PLATFORM_IDENTITY_KEY).iloc[0].to_dict()
        )
        platform_label = platform_identity.platform_label

    if deployment_label is None:
        deployment_identity = DeploymentIdentity(
            **reader.read_frame(_DEPLOYMENT_IDENTITY_KEY).iloc[0].to_dict()
        )
        deployment_label = deployment_identity.deployment_label

    return ResolvedIdentity(
        platform_label=platform_label,
        deployment_label=deployment_label,
    )
