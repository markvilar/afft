"""Storage-agnostic read and write interfaces for a deployment bundle."""

from typing import Iterator, Literal, Protocol

import geopandas as gpd
import pandas as pd


class DeploymentBundleReader(Protocol):
    """Read interface for a deployment bundle."""

    def list_frames(self) -> list[str]:
        """List the keys of every plain (non-spatial) frame the bundle
        holds. Disjoint from `list_geoframes`."""
        ...

    def list_geoframes(self) -> list[str]:
        """List the keys of every geoframe the bundle holds. Disjoint from
        `list_frames`."""
        ...

    def has_frame(self, key: str) -> bool:
        """Return whether a frame exists at `key`."""
        ...

    def read_frame(self, key: str) -> pd.DataFrame:
        """
        Read the frame stored at `key`.

        Raises
        ------
        KeyError: If no frame exists at `key`.
        """
        ...

    def is_geoframe(self, key: str) -> bool:
        """
        Return whether the frame at `key` carries a geometry column.

        Raises
        ------
        KeyError: If no frame exists at `key`.
        """
        ...

    def read_geoframe(self, key: str) -> gpd.GeoDataFrame:
        """
        Read the geospatial frame stored at `key`.

        Raises
        ------
        KeyError: If no frame exists at `key`.
        TypeError: If the frame at `key` has no geometry column.
        """
        ...

    def iter_frames(self) -> Iterator[tuple[str, pd.DataFrame]]:
        """Iterate over every plain frame the bundle holds, as `(key,
        frame)` pairs."""
        ...

    def iter_geoframes(self) -> Iterator[tuple[str, gpd.GeoDataFrame]]:
        """Iterate over every geoframe the bundle holds, as `(key,
        geoframe)` pairs."""
        ...

    def contents(self) -> pd.DataFrame:
        """Read the bundle's manifest of frame identifiers."""
        ...


class DeploymentBundleWriter(Protocol):
    """Write interface for a deployment bundle."""

    def has_frame(self, key: str) -> bool:
        """Return whether a frame exists at `key`."""
        ...

    def write_frame(
        self,
        key: str,
        frame: pd.DataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        """
        Write `frame` to the bundle at `key`.

        With `if_exists="replace"`, any existing frame at `key` is
        overwritten.

        Raises
        ------
        ValueError: If `key` already exists and `if_exists="fail"` (the
            default).
        """
        ...

    def write_geoframe(
        self,
        key: str,
        frame: gpd.GeoDataFrame,
        *,
        if_exists: Literal["fail", "replace"] = "fail",
    ) -> None:
        """
        Write `frame` to the bundle at `key`, with the same `if_exists`
        semantics as `write_frame`.

        Raises
        ------
        TypeError: If `frame` is not a `GeoDataFrame`, or has no active
            geometry column set.
        ValueError: If `frame`'s geometry is entirely empty/null, or its
            CRS is not set.
        """
        ...


class DeploymentBundleIO(
    DeploymentBundleReader, DeploymentBundleWriter, Protocol
):
    """
    Read and write interface for a single deployment bundle.

    The union of the read and write interfaces, for consumers that read back
    what they have written and so need both to refer to the same bundle. A
    consumer needing only one of the two should depend on that one.
    """


def iter_frames(
    reader: DeploymentBundleReader,
) -> Iterator[tuple[str, pd.DataFrame]]:
    """Back `DeploymentBundleReader.iter_frames` from `list_frames` and
    `read_frame` alone, so backends need not reimplement it."""
    for key in reader.list_frames():
        yield key, reader.read_frame(key)


def iter_geoframes(
    reader: DeploymentBundleReader,
) -> Iterator[tuple[str, gpd.GeoDataFrame]]:
    """Back `DeploymentBundleReader.iter_geoframes` from `list_geoframes`
    and `read_geoframe` alone, so backends need not reimplement it."""
    for key in reader.list_geoframes():
        yield key, reader.read_geoframe(key)
