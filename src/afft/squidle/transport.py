"""Authenticated HTTP transport for the Squidle+ API."""

import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from types import TracebackType
from typing import Any

import httpx
import tenacity

from afft.utils.log import logger


type MediaObject = dict[str, Any]
type Getter = Callable[[str], Any]

_BASE_URL: str = "https://squidle.org"


@dataclass(slots=True, frozen=True)
class SquidleTransportConfig:
    """
    Request behaviour for SquidleTransport.

    Provides the defaults used by every request. Individual methods accept
    optional overrides that fall back to these values.

    Attributes
    ----------
    timeout: Read timeout in seconds per HTTP request.
    retries: Number of retry attempts on transient errors. 0 disables retries.
    backoff_factor: Base multiplier in seconds for exponential backoff.
    backoff_max: Maximum backoff wait in seconds between retries.
    results_per_page: Number of objects to request per page on list endpoints.
    """

    timeout: float = 30.0
    retries: int = 3
    backoff_factor: float = 1.0
    backoff_max: float = 60.0
    results_per_page: int = 100


def _is_retryable(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code >= 500
    return isinstance(exception, httpx.TransportError)


def _make_retrying(config: SquidleTransportConfig) -> tenacity.Retrying:
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


@dataclass(slots=True, frozen=True)
class Operation:
    """
    Handle to a server-side Squidle+ asynchronous operation.

    A future-like view over a long-running operation: call ``done()`` to check
    completion without blocking, or ``result()`` to block (polling) until the
    result is available. The handle depends only on a ``Getter`` (an
    authenticated GET), not the full client, so the client never waits.

    Attributes
    ----------
    path: The submitted endpoint, used to identify the operation in messages.
    status_url: URL polled to check completion.
    result_url: URL fetched to retrieve the result once available.
    """

    _get: Getter
    path: str
    status_url: str
    result_url: str

    def done(self) -> bool:
        """
        Return whether the operation has finished. Non-blocking.

        Raises
        ------
        RuntimeError: If the operation reports an error status.
        """
        status: MediaObject = self._get(self.status_url)
        if status.get("status") == "error":
            raise RuntimeError(
                f"operation {self.path!r} failed: {status.get('message', '')}"
            )
        return bool(status.get("result_available"))

    def result(
        self,
        timeout: float = 300.0,
        interval: float = 2.0,
    ) -> list[MediaObject]:
        """
        Block until the operation finishes and return its result objects.

        Arguments
        ---------
        timeout: Maximum total time in seconds to await completion.
        interval: Seconds between status polls.

        Returns
        -------
        List of raw result objects.

        Raises
        ------
        RuntimeError: If the operation reports an error status.
        TimeoutError: If the operation does not finish within ``timeout``.
        """
        elapsed: float = 0.0
        while not self.done():
            if elapsed >= timeout:
                raise TimeoutError(
                    f"operation {self.path!r} timed out after {timeout}s"
                )
            time.sleep(interval)
            elapsed += interval
        result: MediaObject = self._get(self.result_url)
        return result.get("objects") or []


class SquidleTransport:
    """
    Authenticated HTTP transport for the Squidle+ REST API.

    Exposes the generic request verbs (``get``, ``get_pages``,
    ``submit_operation``) that the resource functions build on. The
    user-facing fluent surface is the ``SquidleClient`` facade, which wraps a
    transport; resource functions take a transport directly.

    Request behaviour is governed by a SquidleTransportConfig set at
    construction. Individual methods accept optional overrides for endpoints
    that need different tuning.
    """

    def __init__(
        self,
        token: str,
        config: SquidleTransportConfig | None = None,
    ) -> None:
        self._config: SquidleTransportConfig = (
            config or SquidleTransportConfig()
        )
        self._http: httpx.Client = httpx.Client(
            base_url=_BASE_URL,
            headers={"X-auth-token": token},
        )

    def _resolve(self, **overrides: Any) -> SquidleTransportConfig:
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
        config: SquidleTransportConfig,
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
        config: SquidleTransportConfig = self._resolve(
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
        config: SquidleTransportConfig = self._resolve(
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

    def submit_operation(self, path: str) -> Operation:
        """
        Trigger a server-side async operation and return a handle to it.

        Sends a single request to start the operation; does not block or poll.

        Arguments
        ---------
        path: API path that triggers the operation.

        Returns
        -------
        Operation handle for checking completion and retrieving the result.
        """
        task: dict[str, Any] = self.get(path)
        return Operation(
            _get=self.get,
            path=path,
            status_url=task["status_url"],
            result_url=task["result_url"],
        )

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._http.close()

    def __enter__(self) -> "SquidleTransport":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._http.close()
