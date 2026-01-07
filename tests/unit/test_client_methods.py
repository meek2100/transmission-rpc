import json
from unittest import mock

import pytest

from transmission_rpc.client import Client
from transmission_rpc.error import TransmissionError


def test_add_torrent_duplicate(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {"result": "success", "arguments": {"torrent-duplicate": {"id": 1, "name": "test", "hashString": "hash"}}}
        ).encode(),
    )
    res = client.add_torrent("magnet:?xt=urn:btih:hash")
    assert res.id == 1


def test_add_torrent_invalid_response(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Invalid torrent-add response"):
        client.add_torrent("magnet:?xt=urn:btih:hash")


def test_get_torrent_not_found(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": []}}).encode()
    )
    with pytest.raises(KeyError, match="Torrent not found"):
        client.get_torrent(1)


def test_session_stats_legacy(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps(
            {
                "result": "success",
                "arguments": {
                    "session-stats": {
                        "activeTorrentCount": 5,
                        "downloadSpeed": 1000,
                        "pausedTorrentCount": 0,
                        "torrentCount": 5,
                        "uploadSpeed": 1000,
                        "cumulative-stats": {},
                        "current-stats": {},
                    }
                },
            }
        ).encode(),
    )
    assert client.session_stats().active_torrent_count == 5


def test_free_space_path_mismatch(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": {"path": "/other", "size-bytes": 100}}).encode(),
    )
    assert client.free_space("/test") is None


def test_get_group_none(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"group": []}}).encode()
    )
    assert client.get_group("test") is None
