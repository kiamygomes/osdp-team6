from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, MutableMapping
from typing import Any

class Request:
    method: str
    url: Any
    headers: Mapping[str, str]
    content: bytes

    def __init__(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Client:
    def __init__(self, **kwargs: Any) -> None: ...
    def __enter__(self) -> Client: ...
    def __exit__(self, *args: Any) -> None: ...
    def close(self) -> None: ...
    def get(self, url: str, **kwargs: Any) -> Response: ...
    def post(self, url: str, **kwargs: Any) -> Response: ...

class AsyncClient:
    def __init__(
        self,
        *,
        transport: ASGITransport | None = None,
        base_url: str = "",
        **kwargs: Any,
    ) -> None: ...
    async def __aenter__(self) -> AsyncClient: ...
    async def __aexit__(self, *args: Any) -> None: ...
    async def aclose(self) -> None: ...
    async def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Response: ...
    async def post(
        self,
        url: str,
        *,
        json: Any = None,
        data: Any = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Response: ...
    async def put(
        self,
        url: str,
        *,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Response: ...
    async def patch(
        self,
        url: str,
        *,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Response: ...
    async def delete(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> Response: ...

class ASGITransport:
    def __init__(
        self,
        app: Any,
        **kwargs: Any,
    ) -> None: ...

class Response:
    status_code: int
    headers: Mapping[str, str]
    content: bytes
    text: str

    def __init__(
        self,
        status_code: int,
        *,
        json: Any = None,
        content: bytes | None = None,
        text: str | None = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None: ...
    def json(self) -> Any: ...
    def raise_for_status(self) -> None: ...

class HTTPError(Exception): ...
class RequestError(Exception): ...

class HTTPStatusError(HTTPError):
    request: Request
    response: Response

    def __init__(
        self,
        message: str,
        *,
        request: Request,
        response: Response,
    ) -> None: ...

class ConnectError(RequestError): ...
class TimeoutException(RequestError): ...

class Timeout:
    def __init__(
        self,
        timeout: float | None = None,
        *,
        connect: float | None = None,
        read: float | None = None,
        write: float | None = None,
        pool: float | None = None,
    ) -> None: ...
