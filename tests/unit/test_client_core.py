import importlib
import json
import logging
from unittest import mock

import pytest
import urllib3

import transmission_rpc.client
from transmission_rpc.client import Client, _parse_torrent_id, _parse_torrent_ids
from transmission_rpc.constants import RpcMethod
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


@pytest.fixture
def mock_http_client() -> object:
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
def client(mock_http_client: object) -> Client:
    return Client()


def test_client_init_unix(mock_http_client: object) -> None:
    with mock.patch("transmission_rpc.client.UnixHTTPConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        # S108 is now ignored for tests in pyproject.toml
        c = Client(protocol="http+unix", host="/tmp/socket")  # noqa: S108
        assert c._url == "http+unix://localhost:9091/transmission/rpc"  # noqa: SLF001


def test_client_init_https(mock_http_client: object) -> None:
    with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as m:
        m.return_value.request.return_value = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({"result": "success", "arguments": {"rpc-version": 17, "version": "4.0.0"}}).encode(),
        )
        c = Client(protocol="https")
        assert c._url == "https://127.0.0.1:9091/transmission/rpc"  # noqa: SLF001


def test_client_init_invalid_protocol() -> None:
    with pytest.raises(ValueError, match="Unknown protocol"):
        Client(protocol="ftp")  # type: ignore[arg-type]


def test_client_init_logger(mock_http_client: object) -> None:
    with pytest.raises(TypeError):
        Client(logger="not a logger")  # type: ignore[arg-type]


def test_client_timeout_setter(client: Client) -> None:
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout is not None
    assert client.timeout.total == 10.0
    with pytest.raises(TypeError):
        client.timeout = "invalid"  # type: ignore[assignment]
    del client.timeout
    assert client.timeout is not None
    assert client.timeout.total == 30.0


def test_http_query_timeout_error(client: Client) -> None:
    client._Client__http_client.request.side_effect = urllib3.exceptions.TimeoutError  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionTimeoutError):
        client._http_query({}, timeout=1)  # noqa: SLF001


def test_http_query_connection_error(client: Client) -> None:
    client._Client__http_client.request.side_effect = urllib3.exceptions.ConnectionError  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionConnectError):
        client._http_query({}, timeout=1)  # noqa: SLF001


def test_http_query_auth_error(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=401, headers={}, data=b"")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionAuthError):
        client._http_query({}, timeout=1)  # noqa: SLF001


def test_http_query_too_many_requests(client: Client) -> None:
    client._Client__http_client.request.side_effect = [  # type: ignore[attr-defined] # noqa: SLF001
        mock.Mock(status=409, headers={"x-transmission-session-id": "id1"}, data=b""),
        mock.Mock(status=409, headers={"x-transmission-session-id": "id2"}, data=b""),
        mock.Mock(status=409, headers={"x-transmission-session-id": "id3"}, data=b""),
    ]
    with pytest.raises(TransmissionError, match="too much request"):
        client._http_query({}, timeout=1)  # noqa: SLF001


def test_request_invalid_json(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=200, headers={}, data=b"invalid json")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionError, match="failed to parse response as json"):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_request_missing_result(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match="Query failed, response data missing without result"):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_request_failed_result(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_context_manager(client: Client) -> None:
    with client as c:
        assert c is client


def test_deprecated_properties(client: Client) -> None:
    with pytest.warns(DeprecationWarning, match="do not use internal property"):
        _ = client.url
    with pytest.warns(DeprecationWarning, match="do not use internal property"):
        _ = client.torrent_get_arguments
    with pytest.warns(DeprecationWarning, match="do not use internal property"):
        _ = client.session_id
    with pytest.warns(DeprecationWarning, match="do not use internal property"):
        _ = client.raw_session
    with pytest.warns(DeprecationWarning, match=r"use `.get_session\(\).version` instead"):
        _ = client.server_version
    with pytest.warns(DeprecationWarning, match=r"use .get_session\(\).rpc_version_semver instead"):
        _ = client.semver_version
    with pytest.warns(DeprecationWarning, match=r"use .get_session\(\).rpc_version instead"):
        _ = client.rpc_version


def test_parse_torrent_id_invalid_str() -> None:
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id("invalid")


def test_parse_torrent_id_invalid_type() -> None:
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id(1.5)  # type: ignore


def test_parse_torrent_ids_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid torrent id"):
        _parse_torrent_ids(1.5)  # type: ignore


def test_client_init_invalid_timeout(mock_http_client: object) -> None:
    with pytest.raises(TypeError, match="unsupported value"):
        Client(timeout="invalid")  # type: ignore


def test_client_timeout_setter_invalid(client: Client) -> None:
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 10  # type: ignore


def test_request_invalid_method(client: Client) -> None:
    with pytest.raises(TypeError, match="request takes method as string"):
        client._request(1)  # type: ignore # noqa: SLF001


def test_request_invalid_arguments(client: Client) -> None:
    with pytest.raises(TypeError, match="request takes arguments should be dict"):
        client._request("method", arguments="invalid")  # type: ignore # noqa: SLF001


def test_request_require_ids(client: Client) -> None:
    with pytest.raises(ValueError, match="request require ids"):
        client._request("method", require_ids=True)  # type: ignore[arg-type] # noqa: SLF001


def test_client_init_logger_valid(mock_http_client: object) -> None:
    logger = logging.getLogger("test")
    c = Client(logger=logger)
    assert c.logger == logger


def test_client_version_import_error() -> None:
    with mock.patch("importlib.metadata.version", side_effect=ImportError):
        importlib.reload(transmission_rpc.client)
        assert transmission_rpc.client.__version__ == "develop"

    # Restore
    importlib.reload(transmission_rpc.client)
    assert transmission_rpc.client.__version__ != "develop"
