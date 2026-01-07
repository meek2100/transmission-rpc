import json
from typing import Any
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client
from transmission_rpc.constants import RpcMethod
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def test_client_init_invalid_protocol() -> None:
    with pytest.raises(ValueError, match="Unknown protocol"):
        Client(protocol="ftp")  # type: ignore[arg-type]


def test_client_init_logger_error() -> None:
    with pytest.raises(TypeError, match="logger must be instance"):
        Client(logger="not_a_logger")  # type: ignore[arg-type]


def test_timeout_property(client: Client) -> None:
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout is not None
    assert client.timeout.total == 10.0
    del client.timeout
    assert client.timeout is not None
    assert client.timeout.total == 30.0
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 5.0  # type: ignore[assignment]


def test_http_query_connection_error(client: Client) -> None:
    client._Client__http_client.request.side_effect = urllib3.exceptions.ConnectionError("fail")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionConnectError):
        client._http_query({})  # noqa: SLF001


def test_http_query_timeout_error(client: Client) -> None:
    client._Client__http_client.request.side_effect = urllib3.exceptions.TimeoutError("fail")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionTimeoutError):
        client._http_query({})  # noqa: SLF001


def test_http_query_auth_error(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=401, headers={}, data=b"")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionAuthError):
        client._http_query({})  # noqa: SLF001


def test_http_query_too_many_requests(client: Client) -> None:
    conflict_resp = mock.Mock(status=409, headers={"x-transmission-session-id": "new_id"}, data=b"")
    client._Client__http_client.request.side_effect = [conflict_resp, conflict_resp, conflict_resp, conflict_resp]  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionError, match="too much request"):
        client._http_query({})  # noqa: SLF001


def test_request_invalid_json(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(status=200, headers={}, data=b"invalid json")  # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(TransmissionError, match="failed to parse response"):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_request_failure_result(client: Client) -> None:
    client._Client__http_client.request.return_value = mock.Mock(  # type: ignore[attr-defined] # noqa: SLF001
        status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()
    )
    with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
        client._request(RpcMethod.TorrentGet)  # noqa: SLF001


def test_deprecated_properties(client: Client) -> None:
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.url
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.torrent_get_arguments
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.raw_session
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.session_id
    with pytest.warns(DeprecationWarning, match="do not use"):
        _ = client.server_version
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        _ = client.semver_version
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        _ = client.rpc_version


def test_client_init_no_auth(mock_http_client: Any) -> None:
    # mock_http_client fixture mocks HTTPConnectionPool for the whole test session
    # but strictly for tests using `client` fixture?
    # No, fixture scope is function?
    # `mock_http_client` in conftest.py yields mock.
    # So if I request it in arguments, it will be active.
    c = Client(username=None, password=None)
    headers = c._Client__auth_headers  # type: ignore[attr-defined] # noqa: SLF001
    assert "Authorization" not in headers


def test_client_init_timeout(mock_http_client: Any) -> None:
    c = Client(timeout=10.0)
    assert c.timeout is not None
    assert c.timeout.total == 10.0
    c2 = Client(timeout=10)
    assert c2.timeout is not None
    assert c2.timeout.total == 10.0
