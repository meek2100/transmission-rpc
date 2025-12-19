from unittest import mock
import pytest
import json
from transmission_rpc.client import Client, _parse_torrent_id, _parse_torrent_ids
from typing import Generator

@pytest.fixture
def mock_http_client() -> Generator[object, None, None]:
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

def test_parse_torrent_id_invalid_str() -> None:
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id("invalid")

def test_parse_torrent_id_invalid_type() -> None:
    with pytest.raises(ValueError, match="is not valid torrent id"):
        _parse_torrent_id(1.5)  # type: ignore

def test_parse_torrent_ids_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid torrent id"):
        _parse_torrent_ids(1.5) # type: ignore

def test_client_init_invalid_timeout(mock_http_client: object) -> None:
    with pytest.raises(TypeError, match="unsupported value"):
        Client(timeout="invalid") # type: ignore

def test_client_timeout_setter_invalid(client: Client) -> None:
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 10 # type: ignore

def test_request_invalid_method(client: Client) -> None:
    with pytest.raises(TypeError, match="request takes method as string"):
        client._request(1) # type: ignore # noqa: SLF001

def test_request_invalid_arguments(client: Client) -> None:
    with pytest.raises(TypeError, match="request takes arguments should be dict"):
        client._request("method", arguments="invalid") # type: ignore # noqa: SLF001

def test_request_require_ids(client: Client) -> None:
    with pytest.raises(ValueError, match="request require ids"):
        client._request("method", require_ids=True)  # type: ignore[arg-type] # noqa: SLF001
