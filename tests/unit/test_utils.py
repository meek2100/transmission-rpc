import pytest
import pathlib
import contextlib
from typing import Any
from unittest import mock
from transmission_rpc.client import remove_unset_value, _single_str_as_list, ensure_location_str, list_or_none, _try_read_torrent
from tests.util import ServerTooLowError, skip_on

def check_properties(cls: type, obj: Any) -> None:
    for prop in dir(cls):
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)

def test_remove_unset_value():
    from transmission_rpc.client import remove_unset_value

    assert remove_unset_value({"a": 1, "b": None}) == {"a": 1}

def test_single_str_as_list():
    from transmission_rpc.client import _single_str_as_list

    assert _single_str_as_list(None) is None
    assert _single_str_as_list("a") == ["a"]
    assert _single_str_as_list(["a"]) == ["a"]

def test_ensure_location_str():
    # Only test the Path branch as str is trivial
    from transmission_rpc.client import ensure_location_str

    p = pathlib.Path.cwd() / "tmp"
    assert ensure_location_str(p) == str(p)

def test_ensure_location_str_error():
    """Cover ensure_location_str relative path error"""
    from transmission_rpc.client import ensure_location_str

    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match="using relative `pathlib.Path`"):
        ensure_location_str(p)

def test_util_skip_on():
    from tests.util import ServerTooLowError, skip_on

    @skip_on(ServerTooLowError, "reason")
    def func():
        raise ServerTooLowError

    # Calling func should skip
    func()

def test_list_or_none() -> None:
    assert list_or_none(None) is None
    assert list_or_none([1]) == [1]
    assert list_or_none((1,)) == [1]

def test_try_read_torrent_file_url() -> None:
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/a.torrent")
