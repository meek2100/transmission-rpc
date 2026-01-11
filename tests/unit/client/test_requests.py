import json
from typing import Any
from unittest import mock

import pytest
import urllib3

from transmission_rpc.client import Client
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def test_http_query_connection_error() -> None:
    """Verify that connection errors from urllib3 are raised as TransmissionConnectError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = urllib3.exceptions.ConnectionError("fail")
        # Client initialization calls get_session, which triggers the query
        with pytest.raises(TransmissionConnectError):
            Client()


def test_http_query_timeout_error() -> None:
    """Verify that timeout errors from urllib3 are raised as TransmissionTimeoutError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = urllib3.exceptions.TimeoutError("fail")
        with pytest.raises(TransmissionTimeoutError):
            Client()


def test_http_query_auth_error() -> None:
    """Verify that 401/403 responses are raised as TransmissionAuthError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.return_value = mock.Mock(status=401, headers={}, data=b"")
        with pytest.raises(TransmissionAuthError):
            Client()


def test_http_query_too_many_requests() -> None:
    """Verify that the client enforces a retry limit on 409 Conflict responses."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # Client should retry a few times then raise or succeed.
        # If it keeps getting 409, it should eventually fail.
        conflict_resp = mock.Mock(status=409, headers={"x-transmission-session-id": "new_id"}, data=b"")
        mock_req.side_effect = [conflict_resp] * 10

        with pytest.raises(TransmissionError, match="too much request"):
            Client()


def test_request_invalid_json(success_response: Any) -> None:
    """Verify that invalid JSON in the response raises a TransmissionError and logs the exception."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # 1. Init success (must include version info)
        mock_req.side_effect = [
            success_response(),
            # 2. Invalid JSON for get_torrents
            mock.Mock(status=200, headers={}, data=b"invalid json"),
        ]

        c = Client()
        # Enable logging to verify exception logging
        c.logger = mock.Mock()

        with pytest.raises(TransmissionError, match="failed to parse response"):
            c.get_torrents()

        c.logger.exception.assert_called()


def test_request_failure_result(success_response: Any) -> None:
    """Verify that a JSON response with 'result': 'failure' raises a TransmissionError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        # 1. Init success
        mock_req.side_effect = [
            success_response(),
            # 2. Failure response
            mock.Mock(status=200, headers={}, data=json.dumps({"result": "failure", "arguments": {}}).encode()),
        ]

        c = Client()
        with pytest.raises(TransmissionError, match='Query failed with result "failure"'):
            c.get_torrents()


def test_request_missing_result(success_response: Any) -> None:
    """Verify that a response missing the 'result' field raises a TransmissionError."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as mock_req:
        mock_req.side_effect = [
            success_response(),
            mock.Mock(status=200, headers={}, data=json.dumps({"arguments": {}}).encode()),
        ]

        c = Client()
        c.logger = mock.Mock()

        with pytest.raises(TransmissionError, match="missing without result"):
            c.get_torrents()

        c.logger.debug.assert_called()
