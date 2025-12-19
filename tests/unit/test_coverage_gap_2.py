from unittest import mock
import socket
import pytest
import logging
import importlib.metadata
import json
from transmission_rpc._unix_socket import UnixHTTPConnection
from transmission_rpc.client import Client
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

def test_unix_http_connection_timeout() -> None:
    with mock.patch("socket.socket") as mock_sock:
        conn = UnixHTTPConnection("/tmp/socket", timeout=10)
        conn._new_conn()
        mock_sock.return_value.settimeout.assert_called_with(10)

def test_client_init_logger_valid(mock_http_client: object) -> None:
    logger = logging.getLogger("test")
    c = Client(logger=logger)
    assert c.logger == logger

def test_client_version_import_error() -> None:
    # We can't easily force ImportError on an already imported module without reloading.
    # And reloading might break other tests.
    # We will try to mock `importlib.metadata.version` before importing `client`?
    # No, `client` is already imported by `conftest` or other tests.

    # We can try to manually change `__version__` and verify usage?
    # But we want to cover the `except ImportError` block.
    # That block runs at module level import time.
    # To cover it, we must reload the module while `importlib.metadata.version` raises ImportError.

    import transmission_rpc.client
    import importlib

    with mock.patch("importlib.metadata.version", side_effect=ImportError):
        importlib.reload(transmission_rpc.client)
        assert transmission_rpc.client.__version__ == "develop"

    # Restore
    importlib.reload(transmission_rpc.client)
    # verify restored
    assert transmission_rpc.client.__version__ != "develop"
