
class Response:
    status_code: int
    headers: dict[str, str]
    body: bytes

    def __init__(
        self,
        content: bytes | str | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ) -> None: ...
    def set_cookie(
        self,
        key: str,
        value: str = "",
        max_age: int | None = None,
        expires: int | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax",
    ) -> None: ...
    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: str | None = None,
    ) -> None: ...
