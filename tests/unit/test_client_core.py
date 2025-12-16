import json
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client, RpcMethod
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


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
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        # S108 is now ignored for tests in pyproject.toml
        c = Client(protocol="http+unix", host="/tmp/socket")
        assert c._url == "http+unix://localhost:9091/transmission/rpc"


def test_client_init_https(mock_http_client):
    with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        c = Client(protocol="https")
        assert c._url == "https://127.0.0.1:9091/transmission/rpc"


def test_client_init_invalid_protocol():
    with pytest.raises(ValueError, match="Invalid protocol"):
        Client(protocol="ftp")


def test_client_init_logger(mock_http_client):
    with pytest.raises(TypeError):
        Client(logger="not a logger")


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


def test_context_manager(client):
    with client as c:
        assert c is client


def test_deprecated_properties(client):
    with pytest.warns(DeprecationWarning, match="url"):
        _ = client.url
    with pytest.warns(DeprecationWarning, match="torrent_get_arguments"):
        _ = client.torrent_get_arguments
    with pytest.warns(DeprecationWarning, match="session_id"):
        _ = client.session_id
    with pytest.warns(DeprecationWarning, match="raw_session"):
        _ = client.raw_session
    with pytest.warns(DeprecationWarning, match="server_version"):
        _ = client.server_version
    with pytest.warns(DeprecationWarning, match="semver_version"):
        _ = client.semver_version
    with pytest.warns(DeprecationWarning, match="rpc_version"):
        _ = client.rpc_version
