import json
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def client() -> Client:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(
                "utf-8"
            ),
        )
        return Client()


def test_session_stats(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "activeTorrentCount": 1,
                    "downloadSpeed": 1000,
                    "cumulative-stats": {},
                    "current-stats": {},
                },
            }
        ).encode(),
    )
    stats = client.session_stats()
    assert stats.active_torrent_count == 1


def test_session_stats_old(client: Client) -> None:
    """Test compatibility with older Transmission versions that wrap stats in 'session-stats' key."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "session-stats": {
                        "activeTorrentCount": 1,
                        "downloadSpeed": 1000,
                        "cumulative-stats": {},
                        "current-stats": {},
                    }
                },
            }
        ).encode(),
    )
    stats = client.session_stats()
    assert stats.active_torrent_count == 1


def test_set_session_all_args(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )

    # Call set_session with a comprehensive list of arguments to verify
    # parameter mapping and unknown argument pass-through.
    client.set_session(
        alt_speed_down=100,
        alt_speed_enabled=True,
        alt_speed_time_begin=100,
        alt_speed_time_day=1,
        alt_speed_time_enabled=True,
        alt_speed_time_end=200,
        alt_speed_up=100,
        blocklist_enabled=True,
        blocklist_url="http://example.com/blocklist",
        cache_size_mb=10,
        dht_enabled=True,
        default_trackers=["http://tracker.com"],
        download_dir="/tmp/downloads",
        download_queue_enabled=True,
        download_queue_size=5,
        encryption="preferred",
        idle_seeding_limit=30,
        idle_seeding_limit_enabled=True,
        incomplete_dir="/tmp/incomplete",
        incomplete_dir_enabled=True,
        lpd_enabled=True,
        peer_limit_global=200,
        peer_limit_per_torrent=50,
        peer_port=51413,
        peer_port_random_on_start=False,
        pex_enabled=True,
        port_forwarding_enabled=True,
        queue_stalled_enabled=True,
        queue_stalled_minutes=10,
        rename_partial_files=True,
        script_torrent_done_enabled=True,
        script_torrent_done_filename="done.sh",
        seed_queue_enabled=True,
        seed_queue_size=5,
        seed_ratio_limit=2.0,
        seed_ratio_limited=True,
        speed_limit_down=1000,
        speed_limit_down_enabled=True,
        speed_limit_up=1000,
        speed_limit_up_enabled=True,
        start_added_torrents=True,
        trash_original_torrent_files=True,
        utp_enabled=True,
        script_torrent_done_seeding_filename="seeding.sh",
        script_torrent_done_seeding_enabled=True,
        script_torrent_added_enabled=True,
        script_torrent_added_filename="added.sh",
        # Ensure unknown arguments are passed through to kwargs
        unknown_arg="value",
    )

    # Verify the arguments sent to the RPC
    # This ensures that no arguments were dropped during the dictionary construction in client.py
    assert client._Client__http_client.request.called  # type: ignore[attr-defined]
    _, kwargs = client._Client__http_client.request.call_args  # type: ignore[attr-defined]
    sent_args = kwargs["json"]["arguments"]

    # Verify a sampling of mapping logic to ensure keys are transformed correctly (e.g., underscores to hyphens)
    assert sent_args["alt-speed-down"] == 100
    assert sent_args["download-dir"] == "/tmp/downloads"
    assert sent_args["encryption"] == "preferred"
    # 'default_trackers' list should be joined by newlines in the payload
    assert sent_args["default-trackers"] == "http://tracker.com"
    # Ensure the unknown argument was preserved and sent
    assert sent_args["unknown_arg"] == "value"


def test_set_session_encryption_invalid(client: Client) -> None:
    with pytest.raises(ValueError, match="Invalid encryption value"):
        client.set_session(encryption="invalid")  # type: ignore[arg-type]


def test_set_session_warning(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    # Mock older protocol version to trigger warning
    client._Client__protocol_version = 14  # type: ignore[attr-defined]
    with mock.patch.object(client.logger, "warning") as mock_warning:
        client.set_session(default_trackers=["tracker"])
        mock_warning.assert_called()


def test_blocklist_update(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined]
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"blocklist-size": 10}}).encode()
    )
    assert client.blocklist_update() == 10
