import json
import pathlib
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import (
    Client,
    RpcMethod,
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)
from transmission_rpc.constants import Priority
from transmission_rpc.session import Session, SessionStats
from transmission_rpc.torrent import FileStat, PeersFrom, Torrent, Tracker, TrackerStats
from transmission_rpc.types import BitMap, Container, Group, PortTestResult

# --- Mock Client Tests ---


@pytest.fixture
def mock_http_client():
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"rpc-version": 17, "rpc-version-semver": "5.3.0", "version": "4.0.0"},
                }
            ).encode("utf-8"),
        )
        yield m


@pytest.fixture
def client(mock_http_client):
    return Client()


def test_client_init_unix(mock_http_client):
    with mock.patch("transmission_rpc.client.UnixHTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"rpc-version": 17, "rpc-version-semver": "5.3.0", "version": "4.0.0"},
                }
            ).encode("utf-8"),
        )
        c = Client(protocol="http+unix", host="/tmp/socket")
        assert c._url == "http+unix://localhost:9091/transmission/rpc"


def test_client_init_https(mock_http_client):
    with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"rpc-version": 17, "rpc-version-semver": "5.3.0", "version": "4.0.0"},
                }
            ).encode("utf-8"),
        )
        c = Client(protocol="https")
        assert c._url == "https://127.0.0.1:9091/transmission/rpc"


def test_client_init_invalid_protocol():
    with pytest.raises(ValueError):
        Client(protocol="ftp")


def test_client_timeout_setter(client):
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout.total == 10.0
    with pytest.raises(TypeError):
        client.timeout = "invalid"
    del client.timeout
    assert client.timeout.total == 30.0


def test_http_query_timeout_error(client):
    client._Client__http_client.request.side_effect = urllib3.exceptions.TimeoutError
    with pytest.raises(TransmissionTimeoutError):
        client._http_query({}, timeout=1)


def test_http_query_connection_error(client):
    client._Client__http_client.request.side_effect = urllib3.exceptions.ConnectionError
    with pytest.raises(TransmissionConnectError):
        client._http_query({}, timeout=1)


def test_http_query_auth_error(client):
    client._Client__http_client.request.return_value = mock.Mock(status=401, headers={}, data=b"")
    with pytest.raises(TransmissionAuthError):
        client._http_query({}, timeout=1)


def test_http_query_too_many_requests(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=409, headers={"x-transmission-session-id": "new_id"}, data=b""
    )
    client._Client__http_client.request.side_effect = [
        mock.Mock(status=409, headers={"x-transmission-session-id": "id1"}, data=b""),
        mock.Mock(status=409, headers={"x-transmission-session-id": "id2"}, data=b""),
        mock.Mock(status=409, headers={"x-transmission-session-id": "id3"}, data=b""),
    ]
    with pytest.raises(TransmissionError, match="too much request"):
        client._http_query({}, timeout=1)


def test_request_invalid_json(client):
    client._Client__http_client.request.return_value = mock.Mock(status=200, headers={}, data=b"invalid json")
    with pytest.raises(TransmissionError, match="failed to parse response as json"):
        client._request(RpcMethod.TorrentGet)


def test_request_missing_result(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Query failed, response data missing without result"):
        client._request(RpcMethod.TorrentGet)


def test_request_failed_result(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
        client._request(RpcMethod.TorrentGet)


def test_add_torrent_file(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    with mock.patch("builtins.open", mock.mock_open(read_data=b"data")):
        torrent = client.add_torrent(b"data")
        assert torrent.id == 1


def test_add_torrent_duplicate(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    torrent = client.add_torrent(b"data")
    assert torrent.id == 1


def test_add_torrent_invalid_response(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        client.add_torrent(b"data")


def test_session_stats(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "activeTorrentCount": 1,
                    "downloadSpeed": 1000,
                    "pausedTorrentCount": 0,
                    "torrentCount": 1,
                    "uploadSpeed": 500,
                    "cumulative-stats": {},
                    "current-stats": {},
                },
            }
        ).encode(),
    )
    stats = client.session_stats()
    assert stats.active_torrent_count == 1


def test_session_stats_old(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "session-stats": {
                        "activeTorrentCount": 1,
                        "downloadSpeed": 1000,
                        "pausedTorrentCount": 0,
                        "torrentCount": 1,
                        "uploadSpeed": 500,
                        "cumulative-stats": {},
                        "current-stats": {},
                    }
                },
            }
        ).encode(),
    )
    stats = client.session_stats()
    assert stats.active_torrent_count == 1


def test_get_torrent_not_found(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode()
    )
    with pytest.raises(KeyError, match="Torrent not found in result"):
        client.get_torrent(1)


def test_change_torrent_empty(client):
    with pytest.raises(ValueError, match="No arguments to set"):
        client.change_torrent(1)


def test_set_session_encryption_invalid(client):
    with pytest.raises(ValueError, match="Invalid encryption value"):
        client.set_session(encryption="invalid")


def test_ensure_location_str_pathlib_relative():
    from transmission_rpc.client import ensure_location_str

    with pytest.raises(ValueError, match="using relative `pathlib.Path` as remote path is not supported"):
        ensure_location_str(pathlib.Path("relative"))


def test_parse_torrent_id_invalid():
    from transmission_rpc.client import _parse_torrent_id

    with pytest.raises(ValueError):
        _parse_torrent_id(-1)
    with pytest.raises(ValueError):
        _parse_torrent_id("invalid")
    with pytest.raises(ValueError):
        _parse_torrent_id(1.5)


def test_parse_torrent_ids_invalid():
    from transmission_rpc.client import _parse_torrent_ids

    with pytest.raises(ValueError):
        _parse_torrent_ids(object())


def test_try_read_torrent_file_url():
    from transmission_rpc.client import _try_read_torrent

    with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
        _try_read_torrent("file:///tmp/test")


def test_port_test(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"port-is-open": True}}).encode()
    )
    assert client.port_test().port_is_open


def test_free_space_success(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/data", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/data") == 100


def test_free_space_fail(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/other", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/data") is None


def test_get_group(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"group": [{"name": "test"}]}}).encode(),
    )
    assert client.get_group("test").name == "test"


def test_get_group_none(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"group": []}}).encode()
    )
    assert client.get_group("test") is None


def test_get_groups(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"group": [{"name": "test"}]}}).encode(),
    )
    groups = client.get_groups()
    assert "test" in groups


def test_context_manager(client):
    with client as c:
        assert c is client


def test_client_init_logger(mock_http_client):
    with pytest.raises(TypeError):
        Client(logger="not a logger")


def test_deprecated_properties(client):
    with pytest.warns(DeprecationWarning):
        _ = client.url
    with pytest.warns(DeprecationWarning):
        _ = client.torrent_get_arguments
    with pytest.warns(DeprecationWarning):
        _ = client.raw_session
    with pytest.warns(DeprecationWarning):
        _ = client.session_id
    with pytest.warns(DeprecationWarning):
        _ = client.server_version
    with pytest.warns(DeprecationWarning):
        _ = client.semver_version
    with pytest.warns(DeprecationWarning):
        _ = client.rpc_version


def test_add_torrent_kwargs(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}}
        ).encode(),
    )
    client.add_torrent("magnet:?xt=urn:btih:hash", labels=["l1"], sequential_download=True)


def test_move_torrent_data(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.move_torrent_data(1, "/new/path")


def test_rename_torrent_path(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/new/path", "name": "new_name"}}).encode(),
    )
    assert client.rename_torrent_path(1, "/old/path", "new_name") == ("/new/path", "new_name")


def test_queue_ops(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.queue_top(1)
    client.queue_bottom(1)
    client.queue_up(1)
    client.queue_down(1)


def test_session_close(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.session_close()


def test_set_group(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.set_group("g1")


def test_blocklist_update(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"blocklist-size": 10}}).encode()
    )
    assert client.blocklist_update() == 10


def test_get_recently_active_torrents(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {"torrents": [{"id": 1, "name": "n", "hashString": "h"}], "removed": [2]},
            }
        ).encode(),
    )
    active, removed = client.get_recently_active_torrents()
    assert len(active) == 1
    assert removed == [2]


def test_remove_torrent(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.remove_torrent(1)


def test_start_torrent(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.start_torrent(1)
    client.start_torrent(1, bypass_queue=True)


def test_start_all(client):
    client._Client__http_client.request.side_effect = [
        mock.Mock(
            status=200,
            headers={},
            data=json.dumps(
                {
                    "result": "success",
                    "arguments": {"torrents": [{"id": 1, "queuePosition": 1, "name": "n", "hashString": "h"}]},
                }
            ).encode(),
        ),
        mock.Mock(status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()),
    ]
    client.start_all()


def test_stop_torrent(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.stop_torrent(1)


def test_verify_torrent(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.verify_torrent(1)


def test_reannounce_torrent(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.reannounce_torrent(1)


# --- Session Tests ---


def test_set_session_all_args(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
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
        unknown_arg="value",
    )


def test_set_session_warning(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client._Client__protocol_version = 14
    with mock.patch.object(client.logger, "warning") as mock_warning:
        client.set_session(default_trackers=["tracker"])
        mock_warning.assert_called()


# --- Type Tests ---


def test_container_init():
    c = Container(fields={"key": "value"})
    assert c.fields["key"] == "value"


def test_container_getattr():
    c = Container(fields={"key": "value"})
    assert c.get("key") == "value"


def test_container_repr():
    c = Container(fields={"key": "value"})
    assert isinstance(repr(c), str)


def test_session_init():
    s = Session(fields={"version": "2.94"})
    assert s.version == "2.94"


def test_session_stats_init():
    s = SessionStats(fields={"activeTorrentCount": 10})
    assert s.active_torrent_count == 10


def test_torrent_init():
    t = Torrent(fields={"id": 1, "name": "test"})
    assert t.id == 1
    assert t.name == "test"


def test_torrent_getattr():
    t = Torrent(fields={"id": 1, "status": 4})
    assert t.status == "downloading"


def test_group_init():
    g = Group(fields={"name": "test"})
    assert g.name == "test"


def test_file_stat():
    data = {"bytesCompleted": 100, "wanted": True, "priority": 1}
    fs = FileStat(fields=data)
    assert fs.bytesCompleted == 100
    assert fs.wanted is True
    assert fs.priority == 1


def test_tracker():
    data = {"announce": "url", "id": 1, "scrape": "url", "tier": 1}
    t = Tracker(fields=data)
    assert t.announce == "url"
    assert t.id == 1
    assert t.scrape == "url"
    assert t.tier == 1


def test_tracker_stats():
    data = {
        "announce": "url",
        "announceState": 1,
        "downloadCount": 1,
        "hasAnnounced": True,
        "hasScraped": True,
        "host": "host",
        "id": 1,
        "isBackup": False,
        "lastAnnouncePeerCount": 1,
        "lastAnnounceResult": "success",
        "lastAnnounceStartTime": 100,
        "lastAnnounceSucceeded": True,
        "lastAnnounceTime": 100,
        "lastAnnounceTimedOut": False,
        "lastScrapeResult": "success",
        "lastScrapeStartTime": 100,
        "lastScrapeSucceeded": True,
        "lastScrapeTime": 100,
        "lastScrapeTimedOut": False,
        "leecherCount": 1,
        "nextAnnounceTime": 100,
        "nextScrapeTime": 100,
        "scrape": "url",
        "scrapeState": 1,
        "seederCount": 1,
        "tier": 1,
        "sitename": "site",
    }
    t = TrackerStats(fields=data)
    assert t.announce == "url"
    assert t.announce_state == 1
    assert t.download_count == 1
    assert t.has_announced is True
    assert t.has_scraped is True
    assert t.host == "host"
    assert t.id == 1
    assert t.is_backup is False
    assert t.last_announce_peer_count == 1
    assert t.last_announce_result == "success"
    assert t.last_announce_start_time == 100
    assert t.last_announce_succeeded is True
    assert t.last_announce_time == 100
    assert t.last_announce_timed_out is False
    assert t.last_scrape_result == "success"
    assert t.last_scrape_start_time == 100
    assert t.last_scrape_succeeded is True
    assert t.last_scrape_time == 100
    assert t.last_scrape_timed_out is False
    assert t.leecher_count == 1
    assert t.next_announce_time == 100
    assert t.next_scrape_time == 100
    assert t.scrape == "url"
    assert t.scrape_state == 1
    assert t.seeder_count == 1
    assert t.tier == 1
    assert t.site_name == "site"


def test_peers_from():
    data = {
        "fromCache": 1,
        "fromDht": 2,
        "fromIncoming": 3,
        "fromLpd": 4,
        "fromLtep": 5,
        "fromPex": 6,
        "fromTracker": 7,
    }
    p = PeersFrom(fields=data)
    assert p.from_cache == 1
    assert p.from_dht == 2
    assert p.from_incoming == 3
    assert p.from_lpd == 4
    assert p.from_ltep == 5
    assert p.from_pex == 6
    assert p.from_tracker == 7


def test_group():
    data = {
        "name": "group",
        "honorsSessionLimits": True,
        "speed-limit-down-enabled": True,
        "speed-limit-down": 100,
        "speed-limit-up-enabled": True,
        "speed-limit-up": 100,
    }
    g = Group(fields=data)
    assert g.name == "group"
    assert g.honors_session_limits is True
    assert g.speed_limit_down_enabled is True
    assert g.speed_limit_down == 100
    assert g.speed_limit_up_enabled is True
    assert g.speed_limit_up == 100


def test_port_test_result():
    data = {"port-is-open": True, "ip_protocol": "ipv4"}
    r = PortTestResult(fields=data)
    assert r.port_is_open is True
    assert r.ip_protocol == "ipv4"


def test_bitmap():
    # 1000 0000 -> 128
    b = BitMap(b"\x80")
    assert b.get(0) is True
    assert b.get(1) is False
    assert b.get(8) is False  # Out of index


def test_session_properties():
    data = {
        "alt-speed-down": 100,
        "alt-speed-enabled": True,
        "alt-speed-time-begin": 100,
        "alt-speed-time-day": 1,
        "alt-speed-time-enabled": True,
        "alt-speed-time-end": 200,
        "alt-speed-up": 100,
        "blocklist-enabled": True,
        "blocklist-size": 10,
        "blocklist-url": "url",
        "cache-size-mb": 10,
        "config-dir": "dir",
        "dht-enabled": True,
        "download-dir": "dir",
        "download-dir-free-space": 1000,
        "download-queue-enabled": True,
        "download-queue-size": 5,
        "encryption": "preferred",
        "idle-seeding-limit": 30,
        "idle-seeding-limit-enabled": True,
        "incomplete-dir": "dir",
        "incomplete-dir-enabled": True,
        "lpd-enabled": True,
        "peer-limit-global": 200,
        "peer-limit-per-torrent": 50,
        "peer-port": 51413,
        "peer-port-random-on-start": False,
        "pex-enabled": True,
        "port-forwarding-enabled": True,
        "queue-stalled-enabled": True,
        "queue-stalled-minutes": 10,
        "rename-partial-files": True,
        "rpc-version": 17,
        "rpc-version-semver": "5.3.0",
        "rpc-version-minimum": 15,
        "script-torrent-done-enabled": True,
        "script-torrent-done-filename": "done.sh",
        "seed-queue-enabled": True,
        "seed-queue-size": 5,
        "seedRatioLimit": 2.0,
        "seedRatioLimited": True,
        "speed-limit-down": 1000,
        "speed-limit-down-enabled": True,
        "speed-limit-up": 1000,
        "speed-limit-up-enabled": True,
        "start-added-torrents": True,
        "trash-original-torrent-files": True,
        "utp-enabled": True,
        "version": "4.0.0",
        "script-torrent-added-filename": "added.sh",
        "script-torrent-added-enabled": True,
        "script-torrent-done-seeding-filename": "seeding.sh",
        "script-torrent-done-seeding-enabled": True,
        "default-trackers": "tracker",
        "units": {
            "speed-units": ["a"],
            "speed-bytes": 1,
            "size-units": ["b"],
            "size-bytes": 1,
            "memory-units": ["c"],
            "memory-bytes": 1,
        },
    }
    s = Session(fields=data)

    assert s.alt_speed_down == 100
    assert s.alt_speed_enabled is True
    assert s.alt_speed_time_begin == 100
    assert s.alt_speed_time_day == 1
    assert s.alt_speed_time_enabled is True
    assert s.alt_speed_time_end == 200
    assert s.alt_speed_up == 100
    assert s.blocklist_enabled is True
    assert s.blocklist_size == 10
    assert s.blocklist_url == "url"
    assert s.cache_size_mb == 10
    assert s.config_dir == "dir"
    assert s.dht_enabled is True
    assert s.download_dir == "dir"
    assert s.download_dir_free_space == 1000
    assert s.download_queue_enabled is True
    assert s.download_queue_size == 5
    assert s.encryption == "preferred"
    assert s.idle_seeding_limit == 30
    assert s.idle_seeding_limit_enabled is True
    assert s.incomplete_dir == "dir"
    assert s.incomplete_dir_enabled is True
    assert s.lpd_enabled is True
    assert s.peer_limit_global == 200
    assert s.peer_limit_per_torrent == 50
    assert s.peer_port == 51413
    assert s.peer_port_random_on_start is False
    assert s.pex_enabled is True
    assert s.port_forwarding_enabled is True
    assert s.queue_stalled_enabled is True
    assert s.queue_stalled_minutes == 10
    assert s.rename_partial_files is True
    assert s.rpc_version == 17
    assert s.rpc_version_semver == "5.3.0"
    assert s.rpc_version_minimum == 15
    assert s.script_torrent_done_enabled is True
    assert s.script_torrent_done_filename == "done.sh"
    assert s.seed_queue_enabled is True
    assert s.seed_queue_size == 5
    assert s.seed_ratio_limit == 2.0
    assert s.seed_ratio_limited is True
    assert s.speed_limit_down == 1000
    assert s.speed_limit_down_enabled is True
    assert s.speed_limit_up == 1000
    assert s.speed_limit_up_enabled is True
    assert s.start_added_torrents is True
    assert s.trash_original_torrent_files is True
    assert s.utp_enabled is True
    assert s.version == "4.0.0"
    assert s.script_torrent_added_filename == "added.sh"
    assert s.script_torrent_added_enabled is True
    assert s.script_torrent_done_seeding_filename == "seeding.sh"
    assert s.script_torrent_done_seeding_enabled is True
    assert s.default_trackers == ["tracker"]
    assert s.units.speed_units == ["a"]
    assert s.units.speed_bytes == 1
    assert s.units.size_units == ["b"]
    assert s.units.size_bytes == 1
    assert s.units.memory_units == ["c"]
    assert s.units.memory_bytes == 1


def test_session_stats_properties():
    data = {
        "activeTorrentCount": 1,
        "downloadSpeed": 100,
        "pausedTorrentCount": 0,
        "torrentCount": 1,
        "uploadSpeed": 50,
        "cumulative-stats": {
            "downloadedBytes": 1000,
            "filesAdded": 1,
            "secondsActive": 10,
            "sessionCount": 1,
            "uploadedBytes": 500,
        },
        "current-stats": {
            "downloadedBytes": 100,
            "filesAdded": 0,
            "secondsActive": 5,
            "sessionCount": 1,
            "uploadedBytes": 50,
        },
    }
    s = SessionStats(fields=data)
    assert s.active_torrent_count == 1
    assert s.download_speed == 100
    assert s.paused_torrent_count == 0
    assert s.torrent_count == 1
    assert s.upload_speed == 50

    assert s.cumulative_stats.downloaded_bytes == 1000
    assert s.cumulative_stats.uploaded_bytes == 500
    assert s.cumulative_stats.files_added == 1
    assert s.cumulative_stats.session_count == 1
    assert s.cumulative_stats.seconds_active == 10

    assert s.current_stats.downloaded_bytes == 100


def test_torrent_properties():
    data = {
        "activityDate": 100,
        "addedDate": 100,
        "bandwidthPriority": 1,
        "comment": "comment",
        "corruptEver": 0,
        "creator": "creator",
        "dateCreated": 100,
        "desiredAvailable": 100,
        "doneDate": 100,
        "downloadDir": "dir",
        "downloadedEver": 100,
        "downloadLimit": 100,
        "downloadLimited": True,
        "editDate": 100,
        "error": 0,
        "errorString": "",
        "eta": 100,
        "etaIdle": 100,
        "file-count": 1,
        "hashString": "hash",
        "haveUnchecked": 0,
        "haveValid": 0,
        "honorsSessionLimits": True,
        "id": 1,
        "isFinished": True,
        "isPrivate": True,
        "isStalled": False,
        "labels": ["label"],
        "leftUntilDone": 0,
        "magnetLink": "magnet",
        "manualAnnounceTime": 100,
        "maxConnectedPeers": 100,
        "metadataPercentComplete": 1.0,
        "name": "name",
        "peer-limit": 100,
        "peersConnected": 10,
        "peersGettingFromUs": 5,
        "peersSendingToUs": 5,
        "percentDone": 1.0,
        "pieceCount": 100,
        "pieceSize": 1024,
        "priorities": [1],
        "queuePosition": 0,
        "rateDownload": 100,
        "rateUpload": 100,
        "recheckProgress": 0.0,
        "secondsDownloading": 100,
        "secondsSeeding": 100,
        "seedIdleLimit": 30,
        "seedIdleMode": 1,
        "seedRatioLimit": 2.0,
        "seedRatioMode": 1,
        "sizeWhenDone": 1000,
        "startDate": 100,
        "status": 0,
        "torrentFile": "file",
        "totalSize": 1000,
        "uploadLimit": 100,
        "uploadLimited": True,
        "uploadedEver": 100,
        "uploadRatio": 1.0,
        "wanted": [1],
        "webseedsSendingToUs": 0,
        "files": [{"name": "file1", "bytesCompleted": 100, "length": 1000}],
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "trackers": [{"announce": "url", "id": 1, "scrape": "url", "tier": 1}],
        "trackerStats": [
            {
                "announce": "url",
                "announceState": 1,
                "downloadCount": 1,
                "hasAnnounced": True,
                "hasScraped": True,
                "host": "host",
                "id": 1,
                "isBackup": False,
                "lastAnnouncePeerCount": 1,
                "lastAnnounceResult": "success",
                "lastAnnounceStartTime": 100,
                "lastAnnounceSucceeded": True,
                "lastAnnounceTime": 100,
                "lastAnnounceTimedOut": False,
                "lastScrapeResult": "success",
                "lastScrapeStartTime": 100,
                "lastScrapeSucceeded": True,
                "lastScrapeTime": 100,
                "lastScrapeTimedOut": False,
                "leecherCount": 1,
                "nextAnnounceTime": 100,
                "nextScrapeTime": 100,
                "scrape": "url",
                "scrapeState": 1,
                "seederCount": 1,
                "tier": 1,
            }
        ],
        "peers": [
            {
                "address": "1.2.3.4",
                "clientName": "client",
                "clientIsChoked": False,
                "clientIsInterested": True,
                "flagStr": "E",
                "isDownloadingFrom": True,
                "isEncrypted": True,
                "isIncoming": False,
                "isUploadingTo": False,
                "isUTP": False,
                "peerIsChoked": True,
                "peerIsInterested": False,
                "port": 51413,
                "progress": 0.5,
                "rateToClient": 100,
                "rateToPeer": 100,
            }
        ],
        "pieces": "dGVzdA==",
        "group": "group",
        "availability": [1],
        "primary-mime-type": "video/mp4",
        "peersFrom": {
            "fromCache": 1,
            "fromDht": 2,
            "fromIncoming": 3,
            "fromLpd": 4,
            "fromLtep": 5,
            "fromPex": 6,
            "fromTracker": 7,
        },
    }
    t = Torrent(fields=data)
    assert t.id == 1
    assert t.name == "name"
    assert t.status == "stopped"
    assert t.hashString == "hash"
    assert t.hash_string == "hash"
    assert t.activity_date.timestamp() == 100
    assert t.added_date.timestamp() == 100
    assert t.bandwidth_priority == Priority(1)
    assert t.comment == "comment"
    assert t.corrupt_ever == 0
    assert t.creator == "creator"
    # assert t.date_created.timestamp() == 100
    assert t.desired_available == 100
    assert t.done_date.timestamp() == 100
    assert t.download_dir == "dir"
    assert t.downloaded_ever == 100
    assert t.download_limit == 100
    assert t.download_limited is True
    assert t.edit_date.timestamp() == 100
    assert t.error == 0
    assert t.error_string == ""
    assert t.eta.days == 0
    assert t.eta_idle.days == 0
    assert t.file_count == 1
    assert t.have_unchecked == 0
    assert t.have_valid == 0
    assert t.honors_session_limits is True
    assert t.is_finished is True
    assert t.is_private is True
    assert t.is_stalled is False
    assert t.labels == ["label"]
    assert t.left_until_done == 0
    assert t.magnet_link == "magnet"
    assert t.manual_announce_time.timestamp() == 100
    assert t.max_connected_peers == 100
    assert t.metadata_percent_complete == 1.0
    assert t.peer_limit == 100
    assert t.peers_connected == 10
    assert t.peers_getting_from_us == 5
    assert t.peers_sending_to_us == 5
    assert t.percent_done == 1.0
    assert t.piece_count == 100
    assert t.piece_size == 1024
    # assert t.priorities == [1]
    assert t.queue_position == 0
    assert t.rate_download == 100
    assert t.rate_upload == 100
    assert t.recheck_progress == 0.0
    assert t.seconds_downloading == 100
    assert t.seconds_seeding == 100
    assert t.seed_idle_limit == 30
    assert t.seed_idle_mode == 1
    assert t.seed_ratio_limit == 2.0
    assert t.seed_ratio_mode == 1
    assert t.size_when_done == 1000
    assert t.start_date.timestamp() == 100
    assert t.torrent_file == "file"
    assert t.total_size == 1000
    assert t.upload_limit == 100
    assert t.upload_limited is True
    assert t.uploaded_ever == 100
    assert t.upload_ratio == 1.0
    assert t.wanted == [1]
    assert t.webseeds_sending_to_us == 0
    assert len(t.get_files()) == 1
    assert len(t.trackers) == 1
    assert len(t.tracker_stats) == 1
    assert len(t.peers) == 1
    # assert t.pieces == "base64"
    assert t.group == "group"
    # assert t.availability == [1]
    assert t.primary_mime_type == "video/mp4"

    assert t.peers_from.from_cache == 1
    assert t.peers_from.from_dht == 2
    assert t.peers_from.from_incoming == 3
    assert t.peers_from.from_lpd == 4
    assert t.peers_from.from_ltep == 5
    assert t.peers_from.from_pex == 6
    assert t.peers_from.from_tracker == 7


def test_torrent_files():
    data = {
        "id": 1,
        "files": [{"name": "file1", "bytesCompleted": 100, "length": 1000}],
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "priorities": [1],
        "wanted": [1],
    }
    t = Torrent(fields=data)
    files = t.get_files()
    assert len(files) == 1
    f = files[0]
    assert f.name == "file1"
    assert f.completed == 100
    assert f.size == 1000
    assert f.selected is True
    assert f.priority == Priority(1)
