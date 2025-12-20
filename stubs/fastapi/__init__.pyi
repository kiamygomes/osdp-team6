from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

Request = StarletteRequest
Response = StarletteResponse

class FastAPI(Starlette):
    title: str
    version: str

    def __init__(self, **kwargs: Any) -> None: ...
    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def put(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def patch(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
    def add_middleware(
        self,
        middleware_class: type,
        **options: Any,
    ) -> None: ...

class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
    ) -> None: ...

class TestClient:
    def __init__(self, app: Any, **kwargs: Any) -> None: ...
    def __enter__(self) -> TestClient: ...
    def __exit__(self, *args: Any) -> None: ...
    def get(self, url: str, **kwargs: Any) -> Response: ...
    def post(self, url: str, **kwargs: Any) -> Response: ...
    def put(self, url: str, **kwargs: Any) -> Response: ...
    def delete(self, url: str, **kwargs: Any) -> Response: ...
    def patch(self, url: str, **kwargs: Any) -> Response: ...

class Header:
    def __init__(self, default: Any = ..., **kwargs: Any) -> None: ...

class Query:
    def __init__(self, default: Any = ..., **kwargs: Any) -> None: ...

class Path:
    def __init__(self, default: Any = ..., **kwargs: Any) -> None: ...

class Body:
    def __init__(self, default: Any = ..., **kwargs: Any) -> None: ...

class Depends:
    def __init__(
        self,
        dependency: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> None: ...

class Cookie:
    def __init__(self, default: Any = ..., **kwargs: Any) -> None: ...

class status:
    HTTP_200_OK: int
    HTTP_201_CREATED: int
    HTTP_204_NO_CONTENT: int
    HTTP_400_BAD_REQUEST: int
    HTTP_401_UNAUTHORIZED: int
    HTTP_403_FORBIDDEN: int
    HTTP_404_NOT_FOUND: int
    HTTP_500_INTERNAL_SERVER_ERROR: int
