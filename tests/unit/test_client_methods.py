import json
import pathlib
from unittest import mock

import pytest

from transmission_rpc.client import Client, ensure_location_str
from transmission_rpc.error import TransmissionError


@pytest.fixture
def client() -> Client:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        return Client()


def test_add_torrent_file(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    with mock.patch("builtins.open", mock.mock_open(read_data=b"data")):
        torrent = client.add_torrent(b"data")
        assert torrent.id == 1


def test_add_torrent_duplicate(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "h"}}}
        ).encode(),
    )
    torrent = client.add_torrent(b"data")
    assert torrent.id == 1


def test_add_torrent_kwargs(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}}
        ).encode(),
    )
    client.add_torrent("magnet:?xt=urn:btih:hash", labels=["l1"], sequential_download=True)


def test_add_torrent_invalid_response(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        client.add_torrent(b"data")


def test_get_torrent_not_found(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode()
    )
    with pytest.raises(KeyError, match="Torrent not found in result"):
        client.get_torrent(1)


def test_change_torrent_empty(client: Client) -> None:
    with pytest.raises(ValueError, match="No arguments to set"):
        client.change_torrent(1)


def test_rename_torrent_path(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/new/path", "name": "new_name"}}).encode(),
    )
    assert client.rename_torrent_path(1, "/old/path", "new_name") == ("/new/path", "new_name")


def test_move_torrent_data(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.move_torrent_data(1, "/new/path")


def test_start_torrent_bypass(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.start_torrent(1, bypass_queue=True)


def test_start_all(client: Client) -> None:
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined] # noqa: SLF001
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


def test_get_recently_active_torrents(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
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


def test_port_test(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"port-is-open": True}}).encode()
    )
    assert client.port_test().port_is_open


def test_free_space_success(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/data", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/data") == 100


def test_free_space_fail(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/other", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/data") is None


def test_get_group(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"group": [{"name": "test"}]}}).encode(),
    )
    assert client.get_group("test").name == "test"  # type: ignore[union-attr]


def test_get_group_none(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"group": []}}).encode()
    )
    assert client.get_group("test") is None


def test_get_groups(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"group": [{"name": "test"}]}}).encode(),
    )
    groups = client.get_groups()
    assert "test" in groups


def test_ensure_location_str_pathlib_relative() -> None:
    # RUF043: Added raw string prefix 'r' to match pattern
    with pytest.raises(ValueError, match=r"using relative `pathlib.Path` as remote path is not supported"):
        ensure_location_str(pathlib.Path("relative"))


@pytest.mark.parametrize(
    ("method", "args"),
    [
        ("start_torrent", [1]),
        ("stop_torrent", [1]),
        ("verify_torrent", [1]),
        ("reannounce_torrent", [1]),
        ("queue_top", [1]),
        ("queue_bottom", [1]),
        ("queue_up", [1]),
        ("queue_down", [1]),
        ("session_close", []),
        ("set_group", ["g1"]),
        ("remove_torrent", [1]),
    ],
)
def test_void_methods(client: Client, method: str, args: list[object]) -> None:
    """Parametrized test for methods that perform an action and return success with no data."""
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    getattr(client, method)(*args)
