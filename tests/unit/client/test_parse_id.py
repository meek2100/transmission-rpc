"""
Tests for parsing torrent IDs via the Client API.
Refactored to avoid importing private functions from the client module.
"""

import json
from typing import Any
from unittest import mock

import pytest

from transmission_rpc.client import Client


def success_response(arguments: dict[str, Any] | None = None) -> mock.Mock:
    """Helper to create a standard success response mock."""
    return mock.Mock(
        status=200,
        headers={},
        data=json.dumps({"result": "success", "arguments": arguments or {}}).encode(),
    )


@pytest.fixture
def mock_network() -> Any:
    """Fixture to patch urllib3 request."""
    with mock.patch("urllib3.HTTPConnectionPool.request") as m:
        m.return_value = success_response()
        yield m


@pytest.mark.parametrize("arg", [float(1), "non-hash-string"])
def test_parse_id_raise(mock_network: Any, arg: Any) -> None:
    """
    Verify that invalid torrent IDs raise ValueError.
    We use start_torrent to trigger ID parsing validation.
    """
    c = Client()
    with pytest.raises(ValueError, match="torrent id"):
        c.start_torrent(ids=arg)


@pytest.mark.parametrize(
    ("arg", "expected_ids"),
    [
        ("recently-active", "recently-active"),
        ("51ba7d0dd45ab9b9564329c33f4f97493b677924", ["51ba7d0dd45ab9b9564329c33f4f97493b677924"]),
        ((2, "51ba7d0dd45ab9b9564329c33f4f97493b677924"), [2, "51ba7d0dd45ab9b9564329c33f4f97493b677924"]),
        (3, [3]),
        (None, []),
    ],
)
def test_parse_torrent_ids_structure(mock_network: Any, arg: Any, expected_ids: Any) -> None:
    """
    Verify that passing various ID formats results in the correct 'ids' argument in the RPC call.
    """
    c = Client()

    # start_torrent(ids=None) raises ValueError "request require ids" because
    # the internal parser returns [] which is then rejected by require_ids=True.
    if expected_ids == []:
        with pytest.raises(ValueError, match="request require ids"):
            c.start_torrent(ids=arg)
        return

    c.start_torrent(ids=arg)

    # Check what was sent to the network
    sent_json = mock_network.call_args[1]["json"]
    sent_ids = sent_json["arguments"].get("ids")

    assert sent_ids == expected_ids


@pytest.mark.parametrize("arg", ["not-recently-active", "non-hash-string", -1, 1.1, "5:10", "5,6,8,9,10"])
def test_parse_torrent_ids_value_error(mock_network: Any, arg: Any) -> None:
    """
    Verify that invalid ID inputs raise ValueError via the public API.
    """
    c = Client()
    with pytest.raises(ValueError, match="torrent id"):
        c.start_torrent(ids=arg)
