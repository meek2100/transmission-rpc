import pytest

from transmission_rpc.client import _single_str_as_list, _try_read_torrent, list_or_none, remove_unset_value


def test_remove_unset_value() -> None:
    assert remove_unset_value({"a": 1, "b": None}) == {"a": 1}

def test_single_str_as_list() -> None:
    assert _single_str_as_list(None) is None
    assert _single_str_as_list("a") == ["a"]
    assert _single_str_as_list(["a"]) == ["a"]

def test_list_or_none() -> None:
    assert list_or_none(None) is None
    assert list_or_none([1]) == [1]
    assert list_or_none((1,)) == [1]

def test_try_read_torrent_file_url() -> None:
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/a.torrent")
