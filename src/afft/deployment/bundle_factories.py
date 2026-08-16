"""Factories selecting and constructing the concrete deployment bundle
reader/writer behind the storage-agnostic ``Protocol`` interfaces."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from .bundle_gpkg_io import (
    open_deployment_bundle as _open_gpkg_io,
)
from .bundle_gpkg_readers import (
    open_deployment_bundle_reader as _open_gpkg_reader,
)
from .bundle_gpkg_writers import (
    open_deployment_bundle_writer as _open_gpkg_writer,
)
from .bundle_protocols import (
    DeploymentBundleIO,
    DeploymentBundleReader,
    DeploymentBundleWriter,
)


@contextmanager
def open_deployment_bundle(
    path: Path,
) -> Iterator[DeploymentBundleIO]:
    """
    Open a deployment bundle for reading and writing.

    Arguments
    ---------
    path: Path to the deployment bundle file.

    Returns
    -------
    A context manager yielding a ``DeploymentBundleIO``.

    Raises
    ------
    NotImplementedError: If `path`'s suffix is not a supported bundle file
        format.
    """
    match path.suffix:
        case ".gpkg":
            with _open_gpkg_io(path) as bundle:
                yield cast(DeploymentBundleIO, bundle)
        case suffix:
            raise NotImplementedError(
                f"unsupported bundle file suffix {suffix!r}: {path}"
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

    Raises
    ------
    NotImplementedError: If `path`'s suffix is not a supported bundle file
        format.
    """
    match path.suffix:
        case ".gpkg":
            with _open_gpkg_reader(path) as reader:
                yield cast(DeploymentBundleReader, reader)
        case suffix:
            raise NotImplementedError(
                f"unsupported bundle file suffix {suffix!r}: {path}"
            )


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

    Raises
    ------
    NotImplementedError: If `path`'s suffix is not a supported bundle file
        format.
    """
    match path.suffix:
        case ".gpkg":
            with _open_gpkg_writer(path) as writer:
                yield cast(DeploymentBundleWriter, writer)
        case suffix:
            raise NotImplementedError(
                f"unsupported bundle file suffix {suffix!r}: {path}"
            )
