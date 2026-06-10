"""Authenticated HTTP client for the Squidle+ API."""

import time
from types import TracebackType
from typing import Any

import dotenv
import httpx


type MediaObject = dict[str, Any]

_BASE_URL: str = "https://squidle.org"
_TOKEN_KEY: str = "SQUIDLE_API_TOKEN"
_POLL_INTERVAL: float = 2.0
_POLL_TIMEOUT: float = 300.0


class SquidleClient:
    """
    Authenticated HTTP client for the Squidle+ REST API.

    Use as a context manager to ensure the underlying connection is closed:

        with create_client() as client:
            campaigns = fetch_campaigns(client)
    """

    def __init__(self, token: str) -> None:
        self._http: httpx.Client = httpx.Client(
            base_url=_BASE_URL,
            headers={"X-auth-token": token},
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """
        Send a GET request and return the parsed JSON response.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional query parameters.
        timeout: Read timeout in seconds.

        Returns
        -------
        Parsed JSON response.
        """
        response: httpx.Response = self._http.get(
            path, params=params, timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def get_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        results_per_page: int = 100,
        timeout: float = 30.0,
    ) -> list[dict[str, Any]]:
        """
        Fetch all pages from a paginated list endpoint.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional base query parameters.
        results_per_page: Number of objects to request per page.
        timeout: Read timeout in seconds per page request.

        Returns
        -------
        Combined list of all objects across all pages.
        """
        request_params: dict[str, Any] = dict(params or {})
        request_params["results_per_page"] = results_per_page

        objects: list[dict[str, Any]] = []
        page: int = 1

        while True:
            request_params["page"] = page
            data: dict[str, Any] = self.get(
                path, params=request_params, timeout=timeout
            )
            objects.extend(data.get("objects", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1

        return objects

    def export_deployment(
        self,
        deployment_id: int,
        timeout: float = 30.0,
        poll_timeout: float = _POLL_TIMEOUT,
    ) -> list[MediaObject]:
        """
        Trigger and await the async media export for a deployment.

        Starts the background export task, polls until complete, and returns
        the full list of media objects.

        Arguments
        ---------
        deployment_id: Numeric deployment identifier.
        timeout: Read timeout in seconds for each HTTP request.
        poll_timeout: Maximum total time in seconds to wait for the export task.

        Returns
        -------
        List of raw media objects.

        Raises
        ------
        RuntimeError: If the export task fails or times out.
        """
        response: httpx.Response = self._http.get(
            f"/api/deployment/{deployment_id}/export", timeout=timeout
        )
        response.raise_for_status()
        task: dict[str, Any] = response.json()
        status_url: str = task["status_url"]
        result_url: str = task["result_url"]

        elapsed: float = 0.0
        while elapsed < poll_timeout:
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
            status: MediaObject = self.get(status_url, timeout=timeout)
            if status.get("result_available"):
                result: MediaObject = self.get(result_url, timeout=timeout)
                objects: list[MediaObject] = result.get("objects") or []
                return objects
            if status.get("status") == "error":
                raise RuntimeError(
                    f"export task failed for deployment {deployment_id}: "
                    f"{status.get('message', '')}"
                )

        raise RuntimeError(
            f"export task timed out after {poll_timeout}s "
            f"for deployment {deployment_id}"
        )

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._http.close()

    def __enter__(self) -> "SquidleClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._http.close()


def create_client() -> SquidleClient:
    """
    Create a SquidleClient using the API token from .env.

    Returns
    -------
    Authenticated SquidleClient instance.

    Raises
    ------
    ValueError: If SQUIDLE_API_TOKEN is not set in .env.
    """
    token: str | None = dotenv.dotenv_values().get(_TOKEN_KEY)
    if not token:
        raise ValueError(f"missing .env value: '{_TOKEN_KEY}'")
    return SquidleClient(token=token)
