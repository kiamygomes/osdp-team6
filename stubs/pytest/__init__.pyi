from collections.abc import Callable
from typing import Any, TypeVar, overload

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])

class FixtureRequest:
    param: Any

@overload
def fixture(func: _F) -> _F: ...
@overload
def fixture(
    *,
    scope: str = "function",
    params: list[Any] | None = None,
    autouse: bool = False,
    ids: list[str] | None = None,
    name: str | None = None,
) -> Callable[[_F], _F]: ...
def fixture(
    func: _F | None = None,
    *,
    scope: str = "function",
    params: list[Any] | None = None,
    autouse: bool = False,
    ids: list[str] | None = None,
    name: str | None = None,
) -> _F | Callable[[_F], _F]: ...

class MarkDecorator:
    def __call__(self, func: _F) -> _F: ...

class mark:
    @staticmethod
    def asyncio(func: _F) -> _F: ...
    @staticmethod
    def e2e(func: _F) -> _F: ...
    @staticmethod
    def parametrize(
        argnames: str | tuple[str, ...],
        argvalues: list[Any],
        *,
        indirect: bool | list[str] = False,
        ids: list[str] | None = None,
        scope: str | None = None,
    ) -> MarkDecorator: ...
    @staticmethod
    def skip(reason: str | None = None) -> MarkDecorator: ...
    @staticmethod
    def skipif(condition: bool, *, reason: str) -> MarkDecorator: ...

class ContextManager:
    def __enter__(self) -> None: ...
    def __exit__(self, *args: Any) -> None: ...

def raises(
    expected_exception: type[BaseException] | tuple[type[BaseException], ...],
    *,
    match: str | None = None,
) -> ContextManager: ...

def skip(reason: str) -> None: ...
