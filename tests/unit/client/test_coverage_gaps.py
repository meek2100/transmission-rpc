"""
Additional tests to close code coverage gaps.
"""

import json
from typing import Any
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client, _single_str_as_list, list_or_none
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def success_response(arguments: dict[str, Any] | None = None) -> mock.Mock:
    """Helper to create a standard success response mock."""
    args = arguments or {}
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


# --- Previous Coverage Tests ---


def test_session_stats_modern(mock_network: Any) -> None:
    """Verify session_stats works when response is flat (modern)."""
    mock_network.side_effect = [
        success_response(),
        success_response(
            {
                "activeTorrentCount": 5,
                "downloadSpeed": 1000,
                "pausedTorrentCount": 0,
                "torrentCount": 5,
                "uploadSpeed": 1000,
                "cumulative-stats": {},
                "current-stats": {},
            }
        ),
    ]
    c = Client()
    stats = c.session_stats()
    assert stats.active_torrent_count == 5


def test_single_str_as_list_coverage() -> None:
    """Explicitly cover _single_str_as_list helper branches."""
    assert _single_str_as_list(None) is None
    assert _single_str_as_list("test") == ["test"]
    assert _single_str_as_list(["t"]) == ["t"]


def test_list_or_none_coverage() -> None:
    """Explicitly cover list_or_none helper branches."""
    assert list_or_none(None) is None
    assert list_or_none([1]) == [1]


def test_get_group_empty(mock_network: Any) -> None:
    """Verify get_group returns None when result list is empty."""
    mock_network.side_effect = [
        success_response(),
        success_response({"group": []}),
    ]
    c = Client()
    assert c.get_group("missing") is None


def test_add_torrent_unexpected_response(mock_network: Any) -> None:
    """Verify add_torrent raises TransmissionError if response lacks expected keys."""
    mock_network.side_effect = [
        success_response(),
        success_response({"unexpected": "data"}),
    ]
    c = Client()
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        c.add_torrent("magnet:?")


def test_http_query_exceptions_direct(mock_network: Any) -> None:
    """Explicitly test exception mapping in _http_query."""
    # 1. Timeout
    mock_network.side_effect = urllib3.exceptions.TimeoutError("timeout")
    with pytest.raises(TransmissionTimeoutError):
        Client()

    # 2. Connection Error
    mock_network.side_effect = urllib3.exceptions.ConnectionError("connect error")
    with pytest.raises(TransmissionConnectError):
        Client()


def test_read_torrent_file_object(mock_network: Any) -> None:
    """Verify _try_read_torrent handles file-like objects with .read()."""
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    class FileLike:
        def read(self):
            return b"content"

    c.add_torrent(FileLike())
    args = mock_network.call_args[1]["json"]["arguments"]
    assert "metainfo" in args


def test_http_query_retry_limit(mock_network: Any) -> None:
    """Target loop limit in _http_query."""
    conflict = mock.Mock(status=409, headers={"x-transmission-session-id": "new"}, data=b"")
    mock_network.side_effect = [conflict] * 10
    with pytest.raises(TransmissionError, match="too much request"):
        Client()


def test_http_query_auth_error_lines(mock_network: Any) -> None:
    """Target 401/403 check in _http_query."""
    mock_network.return_value = mock.Mock(status=401, headers={"x-header": "v"}, data=b"debug data")
    with pytest.raises(TransmissionAuthError):
        Client()


def test_add_torrent_empty_check(mock_network: Any) -> None:
    """Target empty torrent metadata check."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="Torrent metadata is empty"):
        c.add_torrent(b"")


def test_remove_torrent_call(mock_network: Any) -> None:
    """Target remove_torrent body."""
    mock_network.return_value = success_response()
    c = Client()
    c.remove_torrent(ids=1)
    assert mock_network.called


def test_start_all_call(mock_network: Any) -> None:
    """Target start_all body."""
    mock_network.side_effect = [
        success_response(),
        success_response({"torrents": [{"id": 1, "queuePosition": 0, "hashString": "h"}]}),
        success_response(),
    ]
    c = Client()
    c.start_all()
    assert mock_network.call_count >= 3


def test_port_test_call(mock_network: Any) -> None:
    """Target port_test body."""
    mock_network.side_effect = [success_response(), success_response({"port-is-open": True})]
    c = Client()
    assert c.port_test().port_is_open is True


# --- NEW TESTS for Specific Lines (excluding _request private access) ---


def test_get_torrent_return_found(mock_network: Any) -> None:
    """
    Cover lines 602-603: logic to find and return the specific torrent in get_torrent.
    """
    mock_network.side_effect = [
        success_response(),
        success_response({"torrents": [{"id": 1, "hashString": "hash1", "name": "found"}]}),
    ]
    c = Client()
    # This triggers the 'if ... return Torrent(...)' lines
    t = c.get_torrent(1)
    assert t.id == 1
    assert t.name == "found"


def test_get_torrents_with_arguments(mock_network: Any) -> None:
    """
    Cover lines 617-618: argument set logic in get_torrents.
    """
    mock_network.side_effect = [success_response(), success_response({"torrents": []})]
    c = Client()
    # Passing arguments triggers the 'if arguments:' block
    c.get_torrents(arguments=["name", "id"])

    # Verify we sent the combined set of arguments
    sent_args = mock_network.call_args[1]["json"]["arguments"]["fields"]
    assert "name" in sent_args
    assert "hashString" in sent_args  # Added by the logic


def test_get_recently_active_with_arguments(mock_network: Any) -> None:
    """
    Cover lines 637-638: argument set logic in get_recently_active_torrents.
    """
    mock_network.side_effect = [success_response(), success_response({"torrents": [], "removed": []})]
    c = Client()
    # Passing arguments triggers the 'if arguments:' block
    c.get_recently_active_torrents(arguments=["name"])

    sent_args = mock_network.call_args[1]["json"]["arguments"]["fields"]
    assert "name" in sent_args
    assert "hashString" in sent_args


def test_set_session_default_trackers(mock_network: Any) -> None:
    """
    Cover lines 1034-1035: warning trigger for default_trackers.
    """
    # FIX: Return rpc-version 16 so that default_trackers (req 17) triggers warning
    mock_network.return_value = success_response({"rpc-version": 16, "version": "3.00", "rpc-version-semver": "3.0.0"})
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(default_trackers=["http://tracker.com"])
        mock_warn.assert_called()
