import json
from unittest import mock

import pytest

from transmission_rpc.client import Client


@pytest.fixture
def client():
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(
                "utf-8"
            ),
        )
        return Client()


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
                    "cumulative-stats": {},
                    "current-stats": {},
                },
            }
        ).encode(),
    )
    stats = client.session_stats()
    assert stats.active_torrent_count == 1


def test_set_session_all_args(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    client.set_session(download_dir="/tmp/downloads", peer_limit_global=200)


def test_blocklist_update(client):
    client._Client__http_client.request.return_value = mock.Mock(
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"blocklist-size": 10}}).encode()
    )
    assert client.blocklist_update() == 10
