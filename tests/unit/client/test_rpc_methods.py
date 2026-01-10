"""
Tests for Client RPC methods (start, stop, add, etc.) and version compatibility.
"""

import contextlib
import io
import json
import pathlib
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


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


def test_start_torrent_no_ids(mock_network: Any) -> None:
    """Verify that `start_torrent` raises ValueError if no IDs are provided."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="request require ids"):
        c.start_torrent(ids=[])


def test_start_all_bypass_queue(mock_network: Any) -> None:
    """
    Verify that `start_all(bypass_queue=True)` correctly calls `torrent-start-now`
    after fetching the list of torrents.
    """
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrents": [{"id": 1, "queuePosition": 1, "hashString": "a"}]}),  # get_torrents
        success_response(),  # start
    ]
    c = Client()
    c.start_all(bypass_queue=True)

    # Verify the last call was torrent-start-now
    assert mock_network.call_count == 3
    last_call_json = mock_network.call_args_list[-1][1]["json"]
    assert last_call_json["method"] == "torrent-start-now"


def test_get_torrent_with_args(mock_network: Any) -> None:
    """Verify that `get_torrent` raises KeyError if the requested fields are not returned by the server."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrents": []}),  # get_torrent empty result
    ]
    c = Client()
    with pytest.raises(KeyError):
        c.get_torrent(1, arguments=["id", "name"])


def test_change_torrent_warnings_v1_protocol(mock_network: Any) -> None:
    """Verify warnings are issued when using `change_torrent` features not supported by the current server version."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
    ]

    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, tracker_list=[])
        mock_warn.assert_called()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, group="g")
        mock_warn.assert_called()


def test_change_torrent_no_args(mock_network: Any) -> None:
    """Verify that `change_torrent` raises ValueError if no arguments are provided."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="No arguments to set"):
        c.change_torrent(ids=1)


def test_set_session_warnings_full(mock_network: Any) -> None:
    """Verify warnings are issued when using `set_session` features not supported by the current server version."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
        success_response(),
        success_response(),
    ]

    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_done_seeding_filename="f")
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_done_seeding_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_added_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_session(script_torrent_added_filename="f")
        mock_warn.assert_called()


def test_set_group_warning(mock_network: Any) -> None:
    """Verify warning is issued when using `set_group` on a server version that doesn't support it."""
    # Mock init to return version 1
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
    ]
    c = Client()

    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.set_group("g")
        mock_warn.assert_called()


def test_file_scheme_error(mock_network: Any) -> None:
    """Verify that using the `file://` scheme in `add_torrent` raises a ValueError."""
    mock_network.return_value = success_response()
    c = Client()
    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        c.add_torrent("file:///tmp/test.torrent")


def test_change_torrent_version_warnings(mock_network: Any) -> None:
    """Verify specific warnings for `change_torrent` based on RPC version thresholds."""
    # We need to simulate different versions.
    # Case 1: Version 1 (low)
    mock_network.side_effect = [
        mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "0"},
            data=json.dumps(
                {"result": "success", "arguments": {"rpc-version": 1, "version": "1.0", "rpc-version-semver": "1.0.0"}}
            ).encode(),
        ),
        success_response(),
        success_response(),
        success_response(),
    ]
    c = Client()
    with mock.patch.object(c.logger, "warning") as mock_warn:
        c.change_torrent(ids=1, labels=["a"])
        mock_warn.assert_called()  # v16 required

        c.change_torrent(ids=1, group="g")
        mock_warn.assert_called()  # v17 required

        c.change_torrent(ids=1, tracker_list=[["a"]])
        mock_warn.assert_called()  # v17 required


def test_groups_coverage(mock_network: Any) -> None:
    """Cover `set_group` and `get_groups` functionality."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response(),  # set_group
        success_response({"group": [{"name": "test_g"}]}),  # get_groups
        success_response({"group": [{"name": "test_g"}]}),  # get_group
        success_response({"group": []}),  # get_group missing
        success_response({"group": [{"name": "test_g"}]}),  # get_groups list
    ]

    c = Client()

    # Test set_group
    c.set_group("test_g")

    # Test get_groups
    groups = c.get_groups()
    assert "test_g" in groups

    # Test get_group
    g = c.get_group("test_g")
    assert g is not None
    assert g.name == "test_g"

    # Test get_group missing
    assert c.get_group("missing") is None

    # Test get_groups with list
    c.get_groups(["test_g"])
    assert mock_network.call_args[1]["json"]["arguments"]["group"] == ["test_g"]


def test_rpc_command_methods(mock_network: Any) -> None:
    """Verify execution of client command methods."""
    mock_network.side_effect = [
        success_response(),  # init
        # FIX: return a valid torrent for start_all to operate on
        success_response({"torrents": [{"id": 1, "queuePosition": 0, "hashString": "h"}]}),  # start_all (get)
        success_response(),  # start_all (start)
        success_response(),  # stop
        success_response(),  # reannounce
        success_response({"blocklist-size": 10}),  # blocklist
    ]
    c = Client()

    # start_all bypass_queue
    c.start_all(bypass_queue=True)

    # stop_torrent
    c.stop_torrent(ids=1)

    # reannounce_torrent
    c.reannounce_torrent(ids=1)

    # blocklist_update
    assert c.blocklist_update() == 10


def test_add_torrent_args(mock_network: Any) -> None:
    """Cover `add_torrent` arguments serialization."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
    ]

    c = Client()
    c.add_torrent("magnet:?xt=urn:btih:a", labels=["l"], sequential_download=True, bandwidthPriority=1)

    sent_args = mock_network.call_args[1]["json"]["arguments"]
    assert sent_args["labels"] == ["l"]
    assert sent_args["sequential_download"] is True
    assert sent_args["bandwidthPriority"] == 1


def test_misc_rpc_method_edge_cases(mock_network: Any) -> None:
    """Verify edge case handling for invalid session encryption values and other methods."""
    mock_network.return_value = success_response()
    c = Client()

    # set_session invalid encryption
    with pytest.raises(ValueError, match="Invalid encryption value"):
        c.set_session(encryption="invalid")  # type: ignore

    # start_torrent bypass_queue
    c.start_torrent(ids=1, bypass_queue=True)
    sent_json = mock_network.call_args[1]["json"]
    assert sent_json["method"] == "torrent-start-now"

    # free_space success
    mock_network.return_value = success_response({"path": "/tmp", "size-bytes": 100})  # noqa: S108
    assert c.free_space("/tmp") == 100  # noqa: S108

    # free_space fail
    mock_network.return_value = success_response({"path": "/other", "size-bytes": 0})
    assert c.free_space("/tmp") is None  # noqa: S108


def test_add_torrent_types(mock_network: Any) -> None:
    """Cover `add_torrent` with different input types."""
    mock_network.side_effect = [
        success_response(),  # init
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
        success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}),
    ]
    c = Client()

    # bytes
    c.add_torrent(b"torrent content")
    assert "metainfo" in mock_network.call_args[1]["json"]["arguments"]

    # file-like
    f = io.BytesIO(b"torrent content")
    c.add_torrent(f)
    assert "metainfo" in mock_network.call_args[1]["json"]["arguments"]

    # Path (local file)
    p = pathlib.Path("test.torrent")
    with mock.patch("pathlib.Path.read_bytes", return_value=b"content"):
        c.add_torrent(p)
    assert "metainfo" in mock_network.call_args[1]["json"]["arguments"]


def test_add_torrent_empty_metadata_and_unknown_types(mock_network: Any) -> None:
    """Verify `add_torrent` raises ValueError for empty metadata or unknown input types."""
    # FIX: Update return_value to include 'torrent-added' structure
    mock_network.return_value = success_response({"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})
    c = Client()

    # Empty bytes
    with pytest.raises(ValueError, match="Torrent metadata is empty"):
        c.add_torrent(b"")

    # Unknown type
    obj = object()
    c.add_torrent(obj)  # type: ignore
    # Should treat as filename
    assert mock_network.call_args[1]["json"]["arguments"]["filename"] is obj


def test_add_torrent_duplicate(mock_network: Any) -> None:
    """Verify that `add_torrent` handles the 'torrent-duplicate' response correctly."""
    mock_network.side_effect = [
        success_response(),
        success_response({"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}),
    ]
    c = Client()
    res = c.add_torrent("magnet:?xt=urn:btih:hash")
    assert res.id == 1


def test_add_torrent_invalid_response(mock_network: Any) -> None:
    """Verify that `add_torrent` raises TransmissionError if response is invalid."""
    mock_network.side_effect = [success_response(), success_response({})]
    c = Client()
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        c.add_torrent("magnet:?xt=urn:btih:hash")


def test_get_torrent_not_found(mock_network: Any) -> None:
    """Verify that `get_torrent` raises KeyError if the returned list is empty."""
    mock_network.side_effect = [success_response(), success_response({"torrents": []})]
    c = Client()
    with pytest.raises(KeyError, match="Torrent not found"):
        c.get_torrent(1)


def test_session_stats_legacy(mock_network: Any) -> None:
    """Verify `session_stats` compatibility with older response formats."""
    mock_network.side_effect = [
        success_response(),
        success_response(
            {
                "session-stats": {
                    "activeTorrentCount": 5,
                    "downloadSpeed": 1000,
                    "pausedTorrentCount": 0,
                    "torrentCount": 5,
                    "uploadSpeed": 1000,
                    "cumulative-stats": {},
                    "current-stats": {},
                }
            }
        ),
    ]
    c = Client()
    assert c.session_stats().active_torrent_count == 5


def test_parsing_ids_public_api(mock_network: Any) -> None:
    """
    Test ID parsing via public API to avoid calling _parse_torrent_ids directly
    and ensure validation logic is reachable.
    """
    mock_network.return_value = success_response()
    c = Client()

    # Test invalid string length via get_torrent
    with pytest.raises(ValueError, match="not valid torrent id"):
        c.get_torrent("a")  # too short

    # Test invalid string content
    with pytest.raises(ValueError, match="not valid torrent id"):
        c.get_torrent("z" * 40)

    # Test invalid type
    with pytest.raises(ValueError, match="Invalid torrent id"):
        c.start_torrent(ids=1.5)  # type: ignore

    # Test valid hash string
    h = "a" * 40
    mock_network.side_effect = [success_response({"torrents": []})]
    with contextlib.suppress(KeyError):
        c.get_torrent(h)


def test_client_methods_success(mock_network: Any) -> None:
    """
    Verify that various client methods execute without error and return None
    when the server responds with success.
    """
    mock_network.return_value = success_response()
    c = Client()

    c.remove_torrent(ids=1)
    c.start_torrent(ids=1)
    c.stop_torrent(ids=1)
    c.verify_torrent(ids=1)
    c.reannounce_torrent(ids=1)
    c.move_torrent_data(ids=1, location="/tmp")  # noqa: S108
    c.queue_top(ids=1)
    c.queue_bottom(ids=1)
    c.queue_up(ids=1)
    c.queue_down(ids=1)
    c.set_session(alt_speed_enabled=True)
    c.session_close()

    # rename_torrent_path returns tuple
    mock_network.return_value = success_response({"path": "/a", "name": "b"})
    assert c.rename_torrent_path(1, "/path", "name") == ("/a", "b")

    # port_test returns object
    mock_network.return_value = success_response({"port-is-open": True})
    assert c.port_test().port_is_open is True


def test_blocklist_update(mock_network: Any) -> None:
    """Verify blocklist_update returns size."""
    mock_network.side_effect = [success_response(), success_response({"blocklist-size": 123})]
    c = Client()
    assert c.blocklist_update() == 123


def test_get_recently_active_torrents(mock_network: Any) -> None:
    """Verify get_recently_active_torrents structure."""
    mock_network.side_effect = [success_response(), success_response({"torrents": [], "removed": [1, 2]})]
    c = Client()
    _, removed = c.get_recently_active_torrents()
    assert removed == [1, 2]
