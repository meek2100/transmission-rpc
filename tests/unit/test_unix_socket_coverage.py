from unittest import mock
import socket
import pytest
from transmission_rpc._unix_socket import UnixHTTPConnection, UnixHTTPConnectionPool

def test_unix_http_connection() -> None:
    # Mock socket
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket")

        # Test _new_conn
        mock_sock_instance = mock_sock.return_value
        sock = conn._new_conn()

        mock_sock.assert_called_with(socket.AF_UNIX, socket.SOCK_STREAM)
        mock_sock_instance.connect.assert_called_with("/tmp/socket")
        assert sock == mock_sock_instance

def test_unix_http_connection_options() -> None:
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket", socket_options=[(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)])
        conn._new_conn()
        mock_sock.return_value.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

def test_unix_http_connection_pool_str() -> None:
    pool = UnixHTTPConnectionPool(host="/tmp/socket")
    assert str(pool) == "UnixHTTPConnectionPool(host=/tmp/socket)"
