"""
Utility functions and decorators for tests.
"""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import pytest

# Define TypeVars for decorator typing
P = ParamSpec("P")
R = TypeVar("R")


class ServerTooLowError(Exception):
    """Raised when the Transmission server version is too low for a specific feature."""


def skip_on(exception: type[Exception], reason: str = "Default reason") -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to skip a test if a specific exception is raised.

    This is useful for skipping tests that require a newer version of the Transmission daemon
    than what is currently running.

    Args:
        exception: The exception class to check for.
        reason: The reason to display when the test is skipped.

    Returns:
        The decorated function.
    """

    def decorator_func(f: Callable[P, R]) -> Callable[P, R]:
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                # Try to run the test
                return f(*args, **kwargs)
            except exception:
                # If exception of given type happens
                # just swallow it and raise pytest.Skip with given reason
                pytest.skip(reason)
                # Static analysis assistance; pytest.skip raises, but return type must match
                return None  # type: ignore[return-value]

        return wrapper

    return decorator_func
