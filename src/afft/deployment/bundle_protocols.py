"""Storage-agnostic read and write interfaces for a deployment bundle."""

from typing import Literal, Protocol

import pandas as pd


class DeploymentBundleReader(Protocol):
    """Read interface for a deployment bundle."""

    def list_frames(self) -> list[str]:
        """List the keys of every frame the bundle holds."""
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

    def contents(self) -> pd.DataFrame:
        """Read the bundle's `bundle_contents` manifest table directly."""
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
        Write `frame` to the bundle at `key`, creating or updating its
        `bundle_contents` entry.

        Raises if `key` already exists and `if_exists="fail"` (the
        default). With `if_exists="replace"`, any existing frame at `key`
        is overwritten.
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
