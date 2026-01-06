# ruff: noqa: S108
import socket
from unittest import mock

from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool


def test_unix_http_connection() -> None:
    conn = UnixHTTPConnection("/tmp/sock")
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.connect.assert_called_with("/tmp/sock")


def test_unix_http_connection_options() -> None:
    # Test with socket options and timeout
    conn = UnixHTTPConnection(
        "/tmp/sock",
        socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)],
        timeout=10,
    )
    with (
        mock.patch("socket.socket") as mock_socket_cls,
        mock.patch.object(socket, "AF_UNIX", create=True, new=1),
    ):
        mock_sock = mock_socket_cls.return_value
        conn.connect()
        mock_sock.setsockopt.assert_called_with(
            socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1
        )
        mock_sock.settimeout.assert_called_with(10)
        mock_sock.connect.assert_called_with("/tmp/sock")


def test_unix_http_connection_pool_str() -> None:
    pool = UnixHTTPConnectionPool(host="/tmp/sock")
    assert str(pool) == "UnixHTTPConnectionPool(host=/tmp/sock)"
