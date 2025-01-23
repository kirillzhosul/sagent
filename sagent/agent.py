"""Agent module implementation.

Agent - is something like worker with described actions that will be performed in parallel
(single agent orchestration within multiple tasks (workers) or within multiple agents).
"""

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator

from aiohttp import ClientResponse, ClientSession


class _AgentHTTPMixin:
    """Mixin for abstract agent that implements HTTP calls"""

    _http_requests_done: int = 0
    _http_requests_pending: int = 0
    _http_base_url: str | None = None

    @property
    def http_requests_pending(self) -> int:
        return self._http_requests_pending

    @property
    def http_requests_done(self) -> int:
        return self._http_requests_done

    @property
    def http_base_url(self) -> str | None:
        return self._http_base_url

    @http_base_url.setter
    def http_base_url(self, value: str | None) -> None:
        self._http_base_url = value

    @contextmanager
    def _requests_counter_wrapper(self) -> Generator[None, None, None]:
        try:
            self._http_requests_pending += 1
            yield
        finally:
            self._http_requests_pending -= 1
            self._http_requests_done += 1

    async def http(
        self,
        url: str,
        method: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> ClientResponse:
        with self._requests_counter_wrapper():
            async with ClientSession(base_url=self.http_base_url) as session:
                async with session.request(
                    method=method,
                    url=url,
                    ssl=False,
                    json=json,
                    headers=headers,
                ) as response:
                    await response.text()
                    return response


class AbstractAgent(_AgentHTTPMixin, metaclass=ABCMeta):
    """Abstracted agent specifications that should be inherited to declare actions to be performed"""

    def __init__(self) -> None:
        pass

    async def bootstrap(self) -> None: ...

    @abstractmethod
    async def perform(self) -> None:
        """Method that is called when agent should perform actions.

        Override to perform actions you need
        """
