from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

import pytest


class ServerTooLowError(Exception):
    pass


T = TypeVar("T", bound=Callable[..., Any])


def skip_on(exception: type[Exception], reason: str = "Default reason") -> Callable[[T], T]:
    # Func below is the real decorator and will receive the test function as param
    def decorator_func(f: T) -> T:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Try to run the test
                return f(*args, **kwargs)
            except exception:
                # If exception of given type happens
                # just swallow it and raise pytest.Skip with given reason
                pytest.skip(reason)

        return wrapper  # type: ignore[return-value]

    return decorator_func
