from unittest import mock
import pytest
from transmission_rpc import from_url
from typing import Generator
import json

@pytest.fixture
def mock_network() -> Generator[None, None, None]:
    with mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as m_http, \
         mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as m_https, \
         mock.patch("transmission_rpc.client.UnixHTTPConnectionPool") as m_unix:

        # Setup successful response for get_session calls
        mock_resp = mock.Mock(
            status=200,
            headers={"x-transmission-session-id": "session_id"},
            data=json.dumps({
                "result": "success",
                "arguments": {"rpc-version": 17, "version": "4.0.0"}
            }).encode("utf-8")
        )

        m_http.return_value.request.return_value = mock_resp
        m_https.return_value.request.return_value = mock_resp
        m_unix.return_value.request.return_value = mock_resp
        yield

def test_from_url_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="unknown url scheme"):
        from_url("ftp://127.0.0.1")

def test_from_url_unix_no_host() -> None:
    with pytest.raises(ValueError, match="http\\+unix URL is missing Unix socket path"):
        from_url("http+unix://")

def test_from_url_valid_http(mock_network: None) -> None:
    c = from_url("http://127.0.0.1:9091")
    assert c._url == "http://127.0.0.1:9091/transmission/rpc"  # noqa: SLF001

def test_from_url_valid_https(mock_network: None) -> None:
    c = from_url("https://127.0.0.1:9091")
    assert c._url == "https://127.0.0.1:9091/transmission/rpc"  # noqa: SLF001

def test_from_url_valid_unix(mock_network: None) -> None:
    # http+unix://%2Ftmp%2Fsocket/transmission/rpc
    c = from_url("http+unix://%2Ftmp%2Fsocket/transmission/rpc")
    assert c._url == "http+unix://localhost/transmission/rpc"  # noqa: SLF001
