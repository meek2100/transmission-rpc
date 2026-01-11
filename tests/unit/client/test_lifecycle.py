from __future__ import annotations

import importlib
import json
import pathlib
import socket
from typing import Any, Literal
from unittest import mock
from urllib.parse import urljoin

import certifi
import pytest
import urllib3
from urllib3 import Timeout

import transmission_rpc.client
from transmission_rpc import DEFAULT_TIMEOUT, from_url
from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool
from transmission_rpc.client import Client
from transmission_rpc.constants import LOGGER, get_torrent_arguments
from transmission_rpc.error import TransmissionAuthError


@pytest.mark.parametrize(
    ("url", "kwargs"),
    [
        (
            "http://a:b@127.0.0.1:9092/transmission/rpc",
            {
                "protocol": "http",
                "username": "a",
                "password": "b",
                "host": "127.0.0.1",
                "port": 9092,
                "path": "/transmission/rpc",
            },
        ),
        (
            "http://127.0.0.1/transmission/rpc",
            {
                "protocol": "http",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 80,
                "path": "/transmission/rpc",
            },
        ),
        (
            "https://127.0.0.1/tr/transmission/rpc",
            {
                "protocol": "https",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 443,
                "path": "/tr/transmission/rpc",
            },
        ),
        (
            "https://127.0.0.1/",
            {
                "protocol": "https",
                "username": None,
                "password": None,
                "host": "127.0.0.1",
                "port": 443,
                "path": "/",
            },
        ),
        (
            "http+unix://%2Fvar%2Frun%2Ftransmission.sock/transmission/rpc",
            {
                "protocol": "http+unix",
                "username": None,
                "password": None,
                "host": "/var/run/transmission.sock",
                "port": None,
                "path": "/transmission/rpc",
            },
        ),
    ],
)
def test_from_url(url: str, kwargs: dict[str, Any]) -> None:
    """
    Verify that `from_url` correctly parses URLs and initializes the Client with the expected arguments.
    """
    with mock.patch("transmission_rpc.Client") as m:
        from_url(url)
        m.assert_called_once_with(
            **kwargs,
            timeout=DEFAULT_TIMEOUT,
            logger=LOGGER,
        )


def test_from_url_invalid_scheme() -> None:
    """Verify `from_url` raises ValueError for unknown URL schemes."""
    with pytest.raises(ValueError, match="unknown url scheme"):
        from_url("ftp://127.0.0.1")


def test_from_url_http_unix_no_host() -> None:
    """Verify `from_url` raises ValueError for http+unix URLs missing the socket path."""
    with pytest.raises(ValueError, match=r"http\+unix URL is missing Unix socket path"):
        from_url("http+unix://")


def test_client_init_invalid_protocol() -> None:
    """Verify that initializing Client with an invalid protocol raises a ValueError."""
    with pytest.raises(ValueError, match="Unknown protocol"):
        Client(protocol="ftp")  # type: ignore[arg-type]


def test_client_init_logger_error() -> None:
    """Verify that initializing Client with a non-logger object raises a TypeError."""
    with pytest.raises(TypeError, match="logger must be instance"):
        Client(logger="not_a_logger")  # type: ignore[arg-type]


def test_timeout_property(client: Client) -> None:
    """
    Verify that the 'timeout' property works correctly:
    - Setting it updates the internal timeout.
    - Deleting it resets it to the default.
    - Setting an invalid type raises TypeError.
    """
    client.timeout = urllib3.Timeout(10.0)
    assert client.timeout is not None
    assert client.timeout.total == 10.0
    del client.timeout
    assert client.timeout is not None
    assert client.timeout.total == 30.0
    with pytest.raises(TypeError, match="must use Timeout instance"):
        client.timeout = 5.0  # type: ignore[assignment]


def test_deprecated_properties(client: Client) -> None:
    """Verify that accessing deprecated properties emits a DeprecationWarning and returns expected values."""
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert isinstance(client.url, str)
    with pytest.warns(DeprecationWarning, match="do not use"):
        # Verify it matches the constant for the current mocked version (17)
        assert client.torrent_get_arguments == get_torrent_arguments(17)
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert isinstance(client.raw_session, dict)
    with pytest.warns(DeprecationWarning, match="do not use"):
        # Expect session_id from the fixture (mock_http_client in conftest)
        assert client.session_id == "session_id"
    with pytest.warns(DeprecationWarning, match="do not use"):
        assert client.server_version is not None
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        assert client.semver_version is not None
    with pytest.warns(DeprecationWarning, match="use .get_session"):
        assert client.rpc_version == 17


def test_client_init_no_auth(success_response: Any) -> None:
    """Verify that initializing Client without credentials does not set the Authorization header."""
    # We patch make_headers to verify it is NOT called with basic_auth
    with (
        mock.patch("transmission_rpc.client.make_headers", wraps=urllib3.util.make_headers) as mock_make,
        mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as mock_pool,
    ):
        mock_pool.return_value.request.return_value = success_response()
        Client(username=None, password=None)

        # Check calls to make_headers
        # It might be called for user_agent, but should not have basic_auth
        for call in mock_make.call_args_list:
            assert "basic_auth" not in call.kwargs or call.kwargs["basic_auth"] is None


def test_client_init_timeout_parsing() -> None:
    """
    Verify that initializing Client with different timeout types (float, int, Timeout object, None)
    behaves as expected, and raises TypeError for invalid types.
    """
    with mock.patch("transmission_rpc.client.Client.get_session"):
        # Float
        c = Client(timeout=10.0)
        assert c.timeout is not None
        assert c.timeout.total == 10.0

        # Int
        c = Client(timeout=10)
        assert c.timeout is not None
        assert c.timeout.total == 10.0

        # Timeout object
        c = Client(timeout=Timeout(10))
        assert c.timeout is not None
        assert c.timeout.total == 10

        # None
        c = Client(timeout=None)
        assert c.timeout is None

        # Invalid
        with pytest.raises(TypeError, match="unsupported value"):
            Client(timeout="invalid")  # type: ignore[arg-type]


def test_context_manager_error(client: Client) -> None:
    """Verify that exceptions raised within the Client context manager are propagated."""
    with pytest.raises(ValueError, match="test"), client:
        raise ValueError("test")


def test_client_init_http_unix(tmp_path: pathlib.Path) -> None:
    """Cover initialization of http+unix protocol to ensure correct URL construction."""
    socket_path = str(tmp_path / "test")
    with (
        mock.patch("transmission_rpc.client.UnixHTTPConnectionPool"),
        mock.patch.object(Client, "get_session", autospec=True),
    ):
        c = Client(protocol="http+unix", host=socket_path, path="/transmission/")
        # Use public property (deprecated) to verify URL construction
        with pytest.warns(DeprecationWarning, match="do not use"):
            assert c.url == "http+unix://localhost:9091/transmission/rpc"


def test_client_init_path_correction_and_https() -> None:
    """Cover Client init branches including path correction and HTTPS protocol."""
    with mock.patch.object(Client, "get_session", autospec=True):
        # path fix
        c = Client(path="/transmission/")
        with pytest.warns(DeprecationWarning, match="do not use"):
            assert c.url.endswith("/transmission/rpc")

        # HTTPS
        with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as mock_https:
            Client(protocol="https")
            mock_https.assert_called()


def test_session_close_and_context_manager() -> None:
    """Cover remaining client methods (lifecycle parts) like session_close and context manager behavior."""
    with (
        mock.patch.object(Client, "get_session", autospec=True),
        mock.patch("transmission_rpc.client.urllib3.HTTPConnectionPool") as mock_pool,
    ):
        mock_instance = mock_pool.return_value
        c = Client()
        # Mock request for session_close
        mock_instance.request.return_value = mock.Mock(
            status=200,
            headers={},  # FIX: Added headers to satisfy Client response validation
            data=json.dumps({"result": "success", "arguments": {}}).encode(),
        )

        # session_close
        c.session_close()
        # Should have called request with session-close
        assert mock_instance.request.call_count >= 1

        # Context manager
        with c:
            pass
        # Should close the pool
        mock_instance.close.assert_called()


def test_unix_http_connection(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnection` connects to the correct socket path."""
    socket_path = str(tmp_path / "sock")
    conn = UnixHTTPConnection(socket_path)
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.connect.assert_called_with(socket_path)


def test_unix_http_connection_options(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnection` respects socket options and timeouts."""
    socket_path = str(tmp_path / "sock")
    conn = UnixHTTPConnection(
        socket_path,
        socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)],
        timeout=10,
    )
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        mock_sock.settimeout.assert_called_with(10)
        mock_sock.connect.assert_called_with(socket_path)


def test_unix_http_connection_pool_repr(tmp_path: pathlib.Path) -> None:
    """Verify `UnixHTTPConnectionPool` string representation."""
    socket_path = str(tmp_path / "sock")
    pool = UnixHTTPConnectionPool(host=socket_path)
    # Compare lowercased versions to handle Windows path case-insensitivity
    # and urllib3's host normalization.
    assert str(pool).lower() == f"UnixHTTPConnectionPool(host={socket_path})".lower()


@pytest.mark.parametrize(
    ("protocol", "username", "password", "host", "port", "path"),
    [
        (
            "https",
            "a+2da/s a?s=d$",
            "a@as +@45/:&*^",
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
        (
            "http",
            "/",
            None,
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
    ],
)
def test_client_url_construction(
    protocol: Literal["http", "https"], username: str, password: str | None, host: str, port: int, path: str
) -> None:
    """
    Verify that the Client correctly parses the URL from the given parameters.
    """
    with mock.patch.object(Client, "get_session"):
        client = Client(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
            path=path,
        )

        expected_url = f"{protocol}://{host}:{port}{urljoin(path, 'rpc')}"
        with pytest.warns(DeprecationWarning, match="do not use"):
            assert client.url == expected_url


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_raise_unauthorized(status_code: int) -> None:
    """
    Verify that Client raises TransmissionAuthError when the server returns 401 or 403.
    """
    m = mock.Mock(return_value=mock.Mock(status=status_code, data=b""))
    with mock.patch("urllib3.HTTPConnectionPool.request", m), pytest.raises(TransmissionAuthError):
        Client()


def test_client_custom_ca_bundle() -> None:
    """Verify that tls_cert_file is passed to the HTTPSConnectionPool."""
    custom_ca = "/path/to/custom/ca.pem"

    with (
        mock.patch("transmission_rpc.client.Client.get_session"),
        mock.patch("urllib3.HTTPSConnectionPool") as mock_pool,
    ):
        Client(protocol="https", tls_cert_file=custom_ca)

        _, kwargs = mock_pool.call_args
        assert kwargs["ca_certs"] == custom_ca


def test_client_default_ca_bundle() -> None:
    """Verify that we fall back to certifi when no tls_cert_file is provided."""
    with (
        mock.patch("transmission_rpc.client.Client.get_session"),
        mock.patch("urllib3.HTTPSConnectionPool") as mock_pool,
    ):
        Client(protocol="https")

        _, kwargs = mock_pool.call_args
        assert kwargs["ca_certs"] == certifi.where()


def test_client_env_var_ca_bundle(tmp_path: pathlib.Path) -> None:
    """Verify that we fall back to TRANSMISSION_RPC_PY_CERT_FILE if provided."""
    custom_ca = str(tmp_path / "env-ca.pem")

    with mock.patch.dict("os.environ", {"TRANSMISSION_RPC_PY_CERT_FILE": custom_ca}):
        importlib.reload(transmission_rpc.client)

        with (
            mock.patch("transmission_rpc.client.Client.get_session"),
            mock.patch("urllib3.HTTPSConnectionPool") as mock_pool,
        ):
            transmission_rpc.client.Client(protocol="https")

            _, kwargs = mock_pool.call_args
            assert kwargs["ca_certs"] == custom_ca

    importlib.reload(transmission_rpc.client)


def test_client_arg_priority_over_env(tmp_path: pathlib.Path) -> None:
    """Verify that the explicit argument overrides the environment variable."""
    custom_env_ca = str(tmp_path / "env-ca.pem")
    explicit_ca = str(tmp_path / "arg-ca.pem")

    with mock.patch.dict("os.environ", {"TRANSMISSION_RPC_PY_CERT_FILE": custom_env_ca}):
        importlib.reload(transmission_rpc.client)

        with (
            mock.patch("transmission_rpc.client.Client.get_session"),
            mock.patch("urllib3.HTTPSConnectionPool") as mock_pool,
        ):
            transmission_rpc.client.Client(protocol="https", tls_cert_file=explicit_ca)

            _, kwargs = mock_pool.call_args
            assert kwargs["ca_certs"] == explicit_ca

    importlib.reload(transmission_rpc.client)
