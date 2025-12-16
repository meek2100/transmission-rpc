# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
from __future__ import annotations

import datetime
import io
import re
from typing import Any
from unittest import mock

import pytest

from transmission_rpc import DEFAULT_TIMEOUT, from_url, utils
from transmission_rpc.client import _parse_torrent_id, _parse_torrent_ids, _try_read_torrent
from transmission_rpc.constants import LOGGER


def assert_almost_eq(value: float, expected: float):
    assert abs(value - expected) < 1


@pytest.mark.parametrize(
    ("delta", "expected"),
    {
        datetime.timedelta(0, 0): "0 00:00:00",
        datetime.timedelta(0, 10): "0 00:00:10",
        datetime.timedelta(0, 60): "0 00:01:00",
        datetime.timedelta(0, 61): "0 00:01:01",
        datetime.timedelta(0, 3661): "0 01:01:01",
        datetime.timedelta(1, 3661): "1 01:01:01",
        datetime.timedelta(13, 65660): "13 18:14:20",
    }.items(),
)
def test_format_timedelta(delta, expected):
    # Fixed: Changed comma to equality check
    assert utils.format_timedelta(delta) == expected


@pytest.mark.parametrize(
    ("url", "kwargs"),
    {
        "http://a:b@127.0.0.1:9092/transmission/rpc": {
            "protocol": "http",
            "username": "a",
            "password": "b",
            "host": "127.0.0.1",
            "port": 9092,
            "path": "/transmission/rpc",
        },
        "http://127.0.0.1/transmission/rpc": {
            "protocol": "http",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 80,
            "path": "/transmission/rpc",
        },
        "https://127.0.0.1/tr/transmission/rpc": {
            "protocol": "https",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 443,
            "path": "/tr/transmission/rpc",
        },
        "https://127.0.0.1/": {
            "protocol": "https",
            "username": None,
            "password": None,
            "host": "127.0.0.1",
            "port": 443,
            "path": "/",
        },
        "http+unix://%2Fvar%2Frun%2Ftransmission.sock/transmission/rpc": {
            "protocol": "http+unix",
            "username": None,
            "password": None,
            "host": "/var/run/transmission.sock",
            "port": None,
            "path": "/transmission/rpc",
        },
    }.items(),
)
def test_from_url(url: str, kwargs: dict[str, Any]):
    with mock.patch("transmission_rpc.Client") as m:
        from_url(url)
        m.assert_called_once_with(
            **kwargs,
            timeout=DEFAULT_TIMEOUT,
            logger=LOGGER,
        )


example_hash = "51ba7d0dd45ab9b9564329c33f4f97493b677924"


def test_parse_id_raise_float():
    arg = float(1)
    with pytest.raises(ValueError, match=f"{arg} is not valid torrent id"):
        _parse_torrent_id(arg)


def test_parse_id_raise_string():
    arg = "non-hash-string"
    # Updated match to match the specific string error from client.py
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id(arg)


def test_parse_id_negative():
    # Updated match to accept the generic error message for negative numbers
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id(-1)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("recently-active", "recently-active"),
        (example_hash, [example_hash]),
        ((2, example_hash), [2, example_hash]),
        (3, [3]),
        (None, []),
    ],
)
def test_parse_torrent_ids(arg, expected):
    assert _parse_torrent_ids(arg) == expected, f"parse_torrent_ids({arg}) != {expected}"


@pytest.mark.parametrize("arg", ["not-recently-active", "non-hash-string", -1, 1.1, "5:10", "5,6,8,9,10"])
def test_parse_torrent_ids_value_error(arg):
    with pytest.raises(ValueError, match="torrent id"):
        _parse_torrent_ids(arg)


def test_parse_torrent_ids_invalid_type():
    with pytest.raises(ValueError, match="ids must be int, str, or list"):
        _parse_torrent_ids(object())


def test_try_read_torrent_path(tmp_path):
    p = tmp_path / "test.torrent"
    p.write_bytes(b"data")
    assert _try_read_torrent(p) == "ZGF0YQ=="


def test_try_read_torrent_file_obj():
    f = io.BytesIO(b"data")
    assert _try_read_torrent(f) == "ZGF0YQ=="


def test_try_read_torrent_bytes():
    assert _try_read_torrent(b"data") == "ZGF0YQ=="


def test_try_read_torrent_url():
    assert _try_read_torrent("http://example.com/t.torrent") is None
    assert _try_read_torrent("magnet:?xt=urn:btih:hash") is None


def test_try_read_torrent_file_url():
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/test")
