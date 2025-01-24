"""Internal agent mixin for proving agents HTTP capabilities."""

from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Generator, Mapping

from aiohttp import ClientResponse, ClientSession

# TODO(@kirillzhosul): Migrate onto composition instead of inheritance with mixins.
# TODO(@kirillzhosul): Agents with HTTP should has method to control simultaneous calls number via semaphore inside.


class AgentHTTPMixin:
    """Mixin for abstract agents that implements HTTP calls."""

    _stat_http_requests_done: int = 0
    _stat_http_requests_pending: int = 0
    _stat_http_requests_status_codes: defaultdict[int, int]

    _http_bootstrapped: bool = False

    _http_base_url: str | None = None

    def stat_clear_http(self) -> None:
        self._stat_http_requests_status_codes = defaultdict(int)
        self._stat_http_requests_done = 0
        self._stat_http_requests_pending = 0

    @property
    def stat_http_requests_pending(self) -> int:
        """Property that returns amount of pending HTTP requests."""
        return self._stat_http_requests_pending

    @property
    def stat_http_requests_done(self) -> int:
        """Property that returns amount of done HTTP requests."""
        return self._stat_http_requests_done

    @property
    def http_base_url(self) -> str | None:
        """Property that returns base URL for HTTP requests."""
        return self._http_base_url

    @http_base_url.setter
    def http_base_url(self, value: str | None) -> None:
        """Property setter for base URL for HTTP requests."""
        self._http_base_url = value

    @contextmanager
    def _requests_counter_wrapper(self) -> Generator[None, None, None]:
        """Context manager for counting HTTP requests in http calls."""
        try:
            self._stat_http_requests_pending += 1

            # Pass control back to the execution context
            yield
        finally:
            self._stat_http_requests_pending -= 1
            self._stat_http_requests_done += 1

    async def http(
        self,
        url: str,
        method: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        http_session_kwargs: Mapping[str, Any] | None = None,
        http_request_kwargs: Mapping[str, Any] | None = None,
    ) -> ClientResponse:
        if self._http_bootstrapped is False:
            self.stat_clear_http()
            self._http_bootstrapped = True

        with self._requests_counter_wrapper():
            async with ClientSession(
                base_url=self.http_base_url,
                **(http_session_kwargs or dict()),
            ) as session:
                async with session.request(
                    method=method,
                    url=url,
                    ssl=False,
                    json=json,
                    headers=headers,
                    **(http_request_kwargs or dict()),
                ) as response:
                    await response.text()
                    self._stat_http_requests_status_codes[response.status] += 1

                    return response
