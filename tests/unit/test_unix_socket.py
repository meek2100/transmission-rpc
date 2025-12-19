import socket
from unittest import mock

from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool


def test_unix_http_connection() -> None:
    # Mock socket
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket")  # noqa: S108

        # Test _new_conn
        mock_sock_instance = mock_sock.return_value
        sock = conn._new_conn()  # noqa: SLF001

        mock_sock.assert_called_with(socket.AF_UNIX, socket.SOCK_STREAM)
        mock_sock_instance.connect.assert_called_with("/tmp/socket")  # noqa: S108
        assert sock == mock_sock_instance


def test_unix_http_connection_options() -> None:
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket", socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)])  # noqa: S108
        conn._new_conn()  # noqa: SLF001
        mock_sock.return_value.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)


def test_unix_http_connection_timeout() -> None:
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket", timeout=10)  # noqa: S108
        conn._new_conn()  # noqa: SLF001
        mock_sock.return_value.settimeout.assert_called_with(10)


def test_unix_http_connection_pool_str() -> None:
    pool = UnixHTTPConnectionPool(host="/tmp/socket")  # noqa: S108
    assert str(pool) == "UnixHTTPConnectionPool(host=/tmp/socket)"
