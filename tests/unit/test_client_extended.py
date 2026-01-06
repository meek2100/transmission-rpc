import json
from unittest import mock

from transmission_rpc.client import Client


def test_client_void_methods(client: Client) -> None:
    # Set default success response
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {}
    }).encode()

    methods = [
        ("remove_torrent", {"ids": 1}),
        ("start_torrent", {"ids": 1}),
        ("stop_torrent", {"ids": 1}),
        ("verify_torrent", {"ids": 1}),
        ("reannounce_torrent", {"ids": 1}),
        ("move_torrent_data", {"ids": 1, "location": "/tmp"}),
        ("queue_top", {"ids": 1}),
        ("queue_bottom", {"ids": 1}),
        ("queue_up", {"ids": 1}),
        ("queue_down", {"ids": 1}),
        ("set_session", {"alt_speed_enabled": True}),
        ("session_close", {}),
        ("set_group", {"name": "g1"}),
    ]
    for method_name, kwargs in methods:
        getattr(client, method_name)(**kwargs)


def test_change_torrent(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {}
    }).encode()
    client.change_torrent(ids=1, download_limit=100)


def test_rename_torrent_path(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {"path": "/a", "name": "b"}
    }).encode()
    client.rename_torrent_path(1, "/path", "name")


def test_blocklist_update(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {"blocklist-size": 10}
    }).encode()
    assert client.blocklist_update() == 10


def test_port_test(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {"port-is-open": True, "ip_protocol": "ipv4"}
    }).encode()
    assert client.port_test().port_is_open is True


def test_get_recently_active_torrents(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {"torrents": [], "removed": []}
    }).encode()
    client.get_recently_active_torrents()


def test_get_groups(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({  # type: ignore[attr-defined] # noqa: SLF001
        "result": "success", "arguments": {"group": []}
    }).encode()
    client.get_groups()


def test_context_manager() -> None:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200, headers={"x-transmission-session-id": "0"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0", "rpc-version-semver": "5.0"}}).encode()
        )
        with Client():
            pass
        m.return_value.close.assert_called()

def test_start_all(client: Client) -> None:
    client._Client__http_client.request.reset_mock()  # type: ignore[attr-defined] # noqa: SLF001
    # start_all calls get_torrents first to sort by queue position
    client._Client__http_client.request.side_effect = [ # type: ignore[attr-defined] # noqa: SLF001
        # 1. get_torrents response
        mock.Mock(
            status=200, headers={},
            data=json.dumps({
                "result": "success",
                "arguments": {
                    "torrents": [
                        {"id": 1, "queuePosition": 2, "hashString": "a"},
                        {"id": 2, "queuePosition": 1, "hashString": "b"}
                    ]
                }
            }).encode()
        ),
        # 2. torrent-start response
        mock.Mock(
            status=200, headers={},
            data=json.dumps({"result": "success", "arguments": {}}).encode()
        )
    ]
    client.start_all()
    # Should call start with ids [2, 1] because 2 has pos 1, 1 has pos 2.
    # The last call should be start.
    assert client._Client__http_client.request.call_count == 2 # type: ignore[attr-defined] # noqa: SLF001

def test_rpc_version_warning(client: Client) -> None:
    # Set low protocol version
    client._Client__protocol_version = 1 # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client._rpc_version_warning(2) # noqa: SLF001
        mock_warn.assert_called()

def test_set_session_warnings(client: Client) -> None:
    client._Client__protocol_version = 16 # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(default_trackers=["a"])
        mock_warn.assert_called()

def test_change_torrent_warnings(client: Client) -> None:
    client._Client__protocol_version = 15 # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, labels=["a"])
        mock_warn.assert_called()
