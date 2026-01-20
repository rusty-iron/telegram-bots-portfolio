from typing import (
    Any,
    Callable,
    ContextManager,
    Iterable,
    Optional,
    Type,
    TypeVar,
)

_T = TypeVar("_T")

def fixture(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., _T]], Callable[..., _T]]: ...

class _RaisesContext(ContextManager[None]):
    def __init__(
        self,
        expected_exception: Type[BaseException],
        match: Optional[str] | None = ...,
    ) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool: ...

def raises(
    expected_exception: Type[BaseException], match: Optional[str] | None = ...
) -> _RaisesContext: ...

class _MarkDecorator:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def parametrize(
        self,
        argnames: str | Iterable[str],
        argvalues: Iterable[Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...

class mark:
    skip: _MarkDecorator
    skipif: _MarkDecorator
    xfail: _MarkDecorator
    parametrize: Callable[[str | Iterable[str], Iterable[Any], Any], Any]

def approx(
    number: Any, rel: Optional[float] = ..., abs: Optional[float] = ...
) -> Any: ...

__all__ = [
    "fixture",
    "raises",
    "mark",
    "approx",
]
