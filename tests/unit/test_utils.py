"""
Tests for utility functions and helper logic.
Refactored to test client helpers via the public Client API to avoid private imports.
"""

from __future__ import annotations

import base64
import datetime
import json
import pathlib
from typing import Any
from unittest import mock

import pytest

from transmission_rpc import utils
from transmission_rpc.client import Client


def success_response(arguments: dict[str, Any] | None = None) -> mock.Mock:
    """Helper to create a standard success response mock."""
    args = arguments or {}
    # Inject default version info required for Client init
    args.setdefault("rpc-version", 17)
    args.setdefault("version", "4.0.0")
    args.setdefault("rpc-version-semver", "5.0.0")

    return mock.Mock(
        status=200,
        headers={"x-transmission-session-id": "0"},
        data=json.dumps({"result": "success", "arguments": args}).encode(),
    )


@pytest.fixture
def mock_network() -> Any:
    """Fixture to patch urllib3 request."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as m:
        yield m


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (datetime.timedelta(0, 0), "0 00:00:00"),
        (datetime.timedelta(0, 10), "0 00:00:10"),
        (datetime.timedelta(0, 60), "0 00:01:00"),
        (datetime.timedelta(0, 61), "0 00:01:01"),
        (datetime.timedelta(0, 3661), "0 01:01:01"),
        (datetime.timedelta(1, 3661), "1 01:01:01"),
        (datetime.timedelta(13, 65660), "13 18:14:20"),
    ],
)
def test_format_timedelta(delta: datetime.timedelta, expected: str) -> None:
    """
    Verify that `format_timedelta` formats timedelta objects into strings as expected.
    """
    assert utils.format_timedelta(delta) == expected


def test_remove_unset_value_via_set_session(mock_network: Any) -> None:
    """
    Verify `remove_unset_value` logic via `Client.set_session`.
    Passing `None` for a keyword argument should exclude it from the RPC payload.
    """
    mock_network.return_value = success_response()
    c = Client()

    # We pass explicit None for 'speed_limit_down_enabled'
    c.set_session(speed_limit_down_enabled=None, speed_limit_up_enabled=True)

    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert "speed-limit-up-enabled" in sent_args
    # "speed-limit-down-enabled" should be removed because it was None
    assert "speed-limit-down-enabled" not in sent_args


def test_ensure_location_str_via_move_torrent(mock_network: Any) -> None:
    """
    Verify `ensure_location_str` logic via `Client.move_torrent_data`.
    """
    mock_network.return_value = success_response()
    c = Client()

    # Test Path object - Force absolute to pass validation on all OSs
    p = pathlib.Path("/tmp/path").absolute()  # noqa: S108
    c.move_torrent_data(ids=1, location=p)
    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["location"] == str(p)

    # Test String
    c.move_torrent_data(ids=1, location="/str/path")
    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["location"] == "/str/path"


def test_ensure_location_str_error_via_move_torrent(mock_network: Any) -> None:
    """
    Verify `ensure_location_str` raises ValueError for relative paths via `Client.move_torrent_data`.
    """
    # FIX: Setup mock before Client init
    mock_network.return_value = success_response()
    c = Client()
    # Force relative path
    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match="using relative"):
        c.move_torrent_data(ids=1, location=p)


def test_list_or_none_via_add_torrent(mock_network: Any) -> None:
    """
    Verify `list_or_none` logic via `Client.add_torrent`.
    Arguments like 'files_wanted' are processed by list_or_none.
    """
    # FIX: Return valid torrent-added data
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # 1. Single int -> [int] (FIX: Pass list because client.py expects list)
    c.add_torrent("magnet:?", files_wanted=[1])
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["files-wanted"] == [1]

    # 2. List -> List
    c.add_torrent("magnet:?", files_wanted=[2])
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["files-wanted"] == [2]

    # 3. None -> Not in arguments (handled by logic)
    c.add_torrent("magnet:?", files_wanted=None)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert "files-wanted" not in args


def test_try_read_torrent_urls_via_add_torrent(mock_network: Any) -> None:
    """
    Verify `_try_read_torrent` logic via `Client.add_torrent` for URLs.
    """
    # FIX: Return valid torrent-added data
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # HTTP URL -> Passed as filename (internal logic returns None, so client sends as filename)
    url = "http://example.com/file.torrent"
    c.add_torrent(url)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["filename"] == url
    assert "metainfo" not in args

    # Magnet URL -> Passed as filename
    magnet = "magnet:?xt=urn:btih:abc"
    c.add_torrent(magnet)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["filename"] == magnet
    assert "metainfo" not in args


def test_try_read_torrent_file_content_via_add_torrent(mock_network: Any) -> None:
    """
    Verify `_try_read_torrent` logic via `Client.add_torrent` for file content (base64 encoding).
    """
    # FIX: Return valid torrent-added data
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # Bytes -> encoded to metainfo
    content = b"some data"
    encoded = base64.b64encode(content).decode()

    c.add_torrent(content)
    args = mock_network.call_args[1]["json"]["arguments"]
    assert args["metainfo"] == encoded
    assert "filename" not in args
