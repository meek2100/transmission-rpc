import json
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def client():
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        return Client()


def test_add_torrent_duplicate(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "h"}}}
        ).encode(),
    )
    torrent = client.add_torrent(b"data")
    assert torrent.id == 1


def test_rename_torrent_path(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/new/path", "name": "new_name"}}).encode(),
    )
    assert client.rename_torrent_path(1, "/old/path", "new_name") == ("/new/path", "new_name")


def test_start_torrent_bypass(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.start_torrent(1, bypass_queue=True)


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
