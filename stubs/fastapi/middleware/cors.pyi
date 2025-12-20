from typing import Any

from starlette.applications import Starlette

class CORSMiddleware:
    def __init__(
        self,
        app: Starlette,
        allow_origins: list[str] | None = None,
        allow_credentials: bool = False,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        **kwargs: Any,
    ) -> None: ...
