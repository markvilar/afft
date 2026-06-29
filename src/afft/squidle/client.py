"""Authenticated HTTP client for the Squidle+ API."""

import time
from dataclasses import dataclass, replace
from types import TracebackType
from typing import Any

import httpx
import tenacity

from afft.utils.log import logger


type MediaObject = dict[str, Any]

_BASE_URL: str = "https://squidle.org"


@dataclass(slots=True, frozen=True)
class SquidleClientConfig:
    """
    Request behaviour for SquidleClient.

    Provides the defaults used by every request. Individual methods accept
    optional overrides that fall back to these values.

    Attributes
    ----------
    timeout: Read timeout in seconds per HTTP request.
    retries: Number of retry attempts on transient errors. 0 disables retries.
    backoff_factor: Base multiplier in seconds for exponential backoff.
    backoff_max: Maximum backoff wait in seconds between retries.
    results_per_page: Number of objects to request per page on list endpoints.
    poll_interval: Seconds between export task status polls.
    poll_timeout: Maximum total time in seconds to await an export task.
    """

    timeout: float = 30.0
    retries: int = 3
    backoff_factor: float = 1.0
    backoff_max: float = 60.0
    results_per_page: int = 100
    poll_interval: float = 2.0
    poll_timeout: float = 300.0


def _is_retryable(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code >= 500
    return isinstance(exception, httpx.TransportError)


def _make_retrying(config: SquidleClientConfig) -> tenacity.Retrying:
    return tenacity.Retrying(
        stop=tenacity.stop_after_attempt(config.retries + 1),
        wait=tenacity.wait_exponential(
            multiplier=config.backoff_factor,
            min=config.backoff_factor,
            max=config.backoff_max,
        ),
        retry=tenacity.retry_if_exception(_is_retryable),
        before_sleep=tenacity.before_sleep_log(logger, "WARNING"),  # type: ignore[arg-type]
        reraise=True,
    )


class SquidleClient:
    """
    Authenticated HTTP client for the Squidle+ REST API.

    Use as a context manager to ensure the underlying connection is closed:

        with create_client(token) as client:
            campaigns = fetch_campaigns(client)

    Request behaviour is governed by a SquidleClientConfig set at construction.
    Individual methods accept optional overrides for endpoints that need
    different tuning (e.g. a longer poll timeout for large exports).
    """

    def __init__(
        self,
        token: str,
        config: SquidleClientConfig | None = None,
    ) -> None:
        self._config: SquidleClientConfig = config or SquidleClientConfig()
        self._http: httpx.Client = httpx.Client(
            base_url=_BASE_URL,
            headers={"X-auth-token": token},
        )

    def _resolve(self, **overrides: Any) -> SquidleClientConfig:
        """Return the client config with non-None overrides applied."""
        provided: dict[str, Any] = {
            key: value for key, value in overrides.items() if value is not None
        }
        if not provided:
            return self._config
        return replace(self._config, **provided)

    def _request(
        self,
        path: str,
        params: dict[str, Any] | None,
        config: SquidleClientConfig,
    ) -> Any:
        """Send a GET request with retries and return the parsed JSON."""
        for attempt in _make_retrying(config):
            with attempt:
                response: httpx.Response = self._http.get(
                    path, params=params, timeout=config.timeout
                )
                response.raise_for_status()
        return response.json()

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        backoff_factor: float | None = None,
    ) -> Any:
        """
        Send a GET request and return the parsed JSON response.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional query parameters.
        timeout: Override for the configured read timeout in seconds.
        retries: Override for the configured retry attempts.
        backoff_factor: Override for the configured backoff multiplier.

        Returns
        -------
        Parsed JSON response.
        """
        config: SquidleClientConfig = self._resolve(
            timeout=timeout, retries=retries, backoff_factor=backoff_factor
        )
        return self._request(path, params, config)

    def get_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        results_per_page: int | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        backoff_factor: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all pages from a paginated list endpoint.

        Arguments
        ---------
        path: API path relative to the base URL.
        params: Optional base query parameters.
        results_per_page: Override for the configured page size.
        timeout: Override for the configured read timeout in seconds.
        retries: Override for the configured retry attempts per page.
        backoff_factor: Override for the configured backoff multiplier.

        Returns
        -------
        Combined list of all objects across all pages.
        """
        config: SquidleClientConfig = self._resolve(
            results_per_page=results_per_page,
            timeout=timeout,
            retries=retries,
            backoff_factor=backoff_factor,
        )
        request_params: dict[str, Any] = dict(params or {})
        request_params["results_per_page"] = config.results_per_page

        objects: list[dict[str, Any]] = []
        page: int = 1

        while True:
            request_params["page"] = page
            data: dict[str, Any] = self._request(path, request_params, config)
            objects.extend(data.get("objects", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1

        return objects

    def export_deployment(
        self,
        deployment_id: int,
        timeout: float | None = None,
        poll_interval: float | None = None,
        poll_timeout: float | None = None,
        retries: int | None = None,
        backoff_factor: float | None = None,
    ) -> list[MediaObject]:
        """
        Trigger and await the async media export for a deployment.

        Starts the background export task, polls until complete, and returns
        the full list of media objects.

        Arguments
        ---------
        deployment_id: Numeric deployment identifier.
        timeout: Override for the configured read timeout per HTTP request.
        poll_interval: Override for the configured seconds between status polls.
        poll_timeout: Override for the configured maximum export wait.
        retries: Override for the configured retry attempts per request.
        backoff_factor: Override for the configured backoff multiplier.

        Returns
        -------
        List of raw media objects.

        Raises
        ------
        RuntimeError: If the export task fails or times out.
        """
        config: SquidleClientConfig = self._resolve(
            timeout=timeout,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
            retries=retries,
            backoff_factor=backoff_factor,
        )
        for attempt in _make_retrying(config):
            with attempt:
                response: httpx.Response = self._http.get(
                    f"/api/deployment/{deployment_id}/export",
                    timeout=config.timeout,
                )
                response.raise_for_status()
        task: dict[str, Any] = response.json()
        status_url: str = task["status_url"]
        result_url: str = task["result_url"]

        elapsed: float = 0.0
        while elapsed < config.poll_timeout:
            time.sleep(config.poll_interval)
            elapsed += config.poll_interval
            status: MediaObject = self._request(status_url, None, config)
            if status.get("result_available"):
                result: MediaObject = self._request(result_url, None, config)
                objects: list[MediaObject] = result.get("objects") or []
                return objects
            if status.get("status") == "error":
                raise RuntimeError(
                    f"export task failed for deployment {deployment_id}: "
                    f"{status.get('message', '')}"
                )

        raise RuntimeError(
            f"export task timed out after {config.poll_timeout}s "
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


def create_client(
    token: str,
    config: SquidleClientConfig | None = None,
) -> SquidleClient:
    """
    Create a SquidleClient from an API token.

    Arguments
    ---------
    token: Squidle+ API token used to authenticate requests.
    config: Optional request-behaviour configuration. Defaults are used if
        not provided.

    Returns
    -------
    Authenticated SquidleClient instance.
    """
    return SquidleClient(token=token, config=config)
