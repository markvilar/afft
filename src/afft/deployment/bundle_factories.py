"""Factories selecting and constructing the concrete deployment bundle
reader/writer behind the storage-agnostic ``Protocol`` interfaces."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from .bundle_hdf_io import (
    open_deployment_bundle as _open_hdf_io,
)
from .bundle_hdf_readers import (
    open_deployment_bundle_reader as _open_hdf_reader,
)
from .bundle_hdf_writers import (
    open_deployment_bundle_writer as _open_hdf_writer,
)
from .bundle_sqlite_io import (
    open_deployment_bundle as _open_sqlite_io,
)
from .bundle_sqlite_readers import (
    open_deployment_bundle_reader as _open_sqlite_reader,
)
from .bundle_sqlite_writers import (
    open_deployment_bundle_writer as _open_sqlite_writer,
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
        case ".h5":
            with _open_hdf_io(path) as bundle:
                yield cast(DeploymentBundleIO, bundle)
        case ".sqlite":
            with _open_sqlite_io(path) as bundle:
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
        case ".h5":
            with _open_hdf_reader(path) as reader:
                yield cast(DeploymentBundleReader, reader)
        case ".sqlite":
            with _open_sqlite_reader(path) as reader:
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
        case ".h5":
            with _open_hdf_writer(path) as writer:
                yield cast(DeploymentBundleWriter, writer)
        case ".sqlite":
            with _open_sqlite_writer(path) as writer:
                yield cast(DeploymentBundleWriter, writer)
        case suffix:
            raise NotImplementedError(
                f"unsupported bundle file suffix {suffix!r}: {path}"
            )
