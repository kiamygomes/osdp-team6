from typing import Any

from starlette.responses import Response as StarletteResponse

class JSONResponse(StarletteResponse):
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        **kwargs: Any,
    ) -> None: ...

class HTMLResponse(StarletteResponse):
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        **kwargs: Any,
    ) -> None: ...

class PlainTextResponse(StarletteResponse):
    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        **kwargs: Any,
    ) -> None: ...

class RedirectResponse(StarletteResponse):
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        **kwargs: Any,
    ) -> None: ...
