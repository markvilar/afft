"""Factories selecting and constructing the concrete deployment bundle
reader/writer behind the storage-agnostic ``Protocol`` interfaces."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from .bundle_hdf_readers import (
    open_deployment_bundle_reader as _open_hdf_reader,
)
from .bundle_hdf_writers import (
    open_deployment_bundle_writer as _open_hdf_writer,
)
from .bundle_protocols import DeploymentBundleReader, DeploymentBundleWriter

_SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".h5"})


def _check_suffix(path: Path) -> None:
    """
    Raise if `path`'s suffix is not a supported bundle file format.

    Arguments
    ---------
    path: Path to the deployment bundle file.

    Raises
    ------
    ValueError: If `path`'s suffix is not supported.
    """
    if path.suffix not in _SUPPORTED_SUFFIXES:
        raise ValueError(
            f"unsupported bundle file suffix {path.suffix!r}: {path}"
        )


@contextmanager
def open_deployment_bundle_reader(
    path: Path,
) -> Iterator[DeploymentBundleReader]:
    """
    Open a deployment bundle for reading.

    Arguments
    ---------
    path: Path to the deployment bundle file.

    Returns
    -------
    A context manager yielding a ``DeploymentBundleReader``.
    """
    _check_suffix(path)
    with _open_hdf_reader(path) as reader:
        yield cast(DeploymentBundleReader, reader)


@contextmanager
def open_deployment_bundle_writer(
    path: Path,
) -> Iterator[DeploymentBundleWriter]:
    """
    Open a deployment bundle for writing.

    Arguments
    ---------
    path: Path to the deployment bundle file.

    Returns
    -------
    A context manager yielding a ``DeploymentBundleWriter``.
    """
    _check_suffix(path)
    with _open_hdf_writer(path) as writer:
        yield cast(DeploymentBundleWriter, writer)
