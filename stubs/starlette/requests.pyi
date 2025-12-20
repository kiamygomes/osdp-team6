from collections.abc import Awaitable, Callable
from typing import Any

class HTTPConnection:
    scope: dict[str, Any]

class Request(HTTPConnection):
    method: str
    url: Any

    def __init__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]] | None = None,
    ) -> None: ...
    async def json(self) -> Any: ...
    async def body(self) -> bytes: ...
