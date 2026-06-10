"""Authenticated HTTP client for the Squidle+ API."""

import time
from types import TracebackType
from typing import Any

import dotenv
import httpx
import tenacity

from afft.utils.log import logger


type MediaObject = dict[str, Any]

_BASE_URL: str = "https://squidle.org"
_TOKEN_KEY: str = "SQUIDLE_API_TOKEN"
_POLL_INTERVAL: float = 2.0
_POLL_TIMEOUT: float = 300.0
_DEFAULT_RETRIES: int = 3
_DEFAULT_BACKOFF_FACTOR: float = 1.0


def _is_retryable(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code >= 500
    return isinstance(exception, httpx.TransportError)


def _make_retrying(retries: int, backoff_factor: float) -> tenacity.Retrying:
    return tenacity.Retrying(
        stop=tenacity.stop_after_attempt(retries + 1),
        wait=tenacity.wait_exponential(
            multiplier=backoff_factor, min=backoff_factor, max=60.0
        ),
        retry=tenacity.retry_if_exception(_is_retryable),
        before_sleep=tenacity.before_sleep_log(logger, "WARNING"),  # type: ignore[arg-type]
        reraise=True,
    )


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
        retries: int = _DEFAULT_RETRIES,
        backoff_factor: float = _DEFAULT_BACKOFF_FACTOR,
    ) -> Any:
        """
        Send a GET request and return the parsed JSON response.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional query parameters.
        timeout: Read timeout in seconds.
        retries: Number of retry attempts on transient errors. Pass 0 to
            disable retries.
        backoff_factor: Base multiplier in seconds for exponential backoff
            between retries.

        Returns
        -------
        Parsed JSON response.
        """
        for attempt in _make_retrying(retries, backoff_factor):
            with attempt:
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
        retries: int = _DEFAULT_RETRIES,
        backoff_factor: float = _DEFAULT_BACKOFF_FACTOR,
    ) -> list[dict[str, Any]]:
        """
        Fetch all pages from a paginated list endpoint.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional base query parameters.
        results_per_page: Number of objects to request per page.
        timeout: Read timeout in seconds per page request.
        retries: Number of retry attempts per page on transient errors.
        backoff_factor: Base multiplier in seconds for exponential backoff.

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
                path,
                params=request_params,
                timeout=timeout,
                retries=retries,
                backoff_factor=backoff_factor,
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
        retries: int = _DEFAULT_RETRIES,
        backoff_factor: float = _DEFAULT_BACKOFF_FACTOR,
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
        retries: Number of retry attempts on transient errors per request.
        backoff_factor: Base multiplier in seconds for exponential backoff.

        Returns
        -------
        List of raw media objects.

        Raises
        ------
        RuntimeError: If the export task fails or times out.
        """
        for attempt in _make_retrying(retries, backoff_factor):
            with attempt:
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
            status: MediaObject = self.get(
                status_url,
                timeout=timeout,
                retries=retries,
                backoff_factor=backoff_factor,
            )
            if status.get("result_available"):
                result: MediaObject = self.get(
                    result_url,
                    timeout=timeout,
                    retries=retries,
                    backoff_factor=backoff_factor,
                )
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
