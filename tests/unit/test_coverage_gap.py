import json
from typing import Any
from unittest import mock

import pytest
from urllib3 import Timeout

from transmission_rpc.client import Client
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent


def test_client_init_timeout_types(mock_http_client: Any) -> None:
    c = Client(timeout=Timeout(10))
    assert c.timeout is not None
    assert c.timeout.total == 10

    c = Client(timeout=None)
    assert c.timeout is None

    with pytest.raises(TypeError, match="unsupported value"):
        Client(timeout="invalid") # type: ignore[arg-type]

def test_start_torrent_no_ids(client: Client) -> None:
    with pytest.raises(ValueError, match="request require ids"):
        client.start_torrent(ids=[])

def test_start_all_bypass_queue(client: Client) -> None:
    client._Client__http_client.request.reset_mock() # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.side_effect = [ # type: ignore[attr-defined] # noqa: SLF001
        mock.Mock(status=200, headers={}, data=json.dumps({"result": "success", "arguments": {"torrents": [{"id": 1, "queuePosition": 1, "hashString": "a"}]}}).encode()),
        mock.Mock(status=200, headers={}, data=json.dumps({"result": "success", "arguments": {}}).encode())
    ]
    client.start_all(bypass_queue=True)

def test_get_torrent_with_args(client: Client) -> None:
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {"torrents": []}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with pytest.raises(KeyError):
        client.get_torrent(1, arguments=["id", "name"])

def test_change_torrent_warnings_full(client: Client) -> None:
    client._Client__protocol_version = 1 # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, tracker_list=[])
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.change_torrent(ids=1, group="g")
        mock_warn.assert_called()

def test_change_torrent_no_args(client: Client) -> None:
    with pytest.raises(ValueError, match="No arguments to set"):
        client.change_torrent(ids=1)

def test_set_session_warnings_full(client: Client) -> None:
    client._Client__protocol_version = 1 # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_done_seeding_filename="f")
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_done_seeding_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_added_enabled=True)
        mock_warn.assert_called()
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_session(script_torrent_added_filename="f")
        mock_warn.assert_called()

def test_set_group_warning(client: Client) -> None:
    client._Client__protocol_version = 1 # type: ignore[attr-defined] # noqa: SLF001
    client._Client__http_client.request.return_value.data = json.dumps({"result": "success", "arguments": {}}).encode() # type: ignore[attr-defined] # noqa: SLF001
    with mock.patch.object(client.logger, "warning") as mock_warn:
        client.set_group("g")
        mock_warn.assert_called()

def test_torrent_missing_optional_fields() -> None:
    # files present but priorities/wanted missing
    fields = {
        "id": 1,
        "files": [{"length": 1, "name": "f", "bytesCompleted": 0}],
        # "priorities" missing
        # "wanted" missing
    }
    t = Torrent(fields=fields)
    assert len(t.get_files()) == 1
    assert t.get_files()[0].priority is None
    assert t.get_files()[0].selected is None

def test_session_property_explicit() -> None:
    # Coverage for session.py line 370
    s = Session(fields={"script-torrent-done-seeding-enabled": True})
    val = s.script_torrent_done_seeding_enabled
    assert val is True

def test_context_manager_error(client: Client) -> None:
    with pytest.raises(ValueError):
        with client:
            raise ValueError("test")

def test_torrent_status_properties() -> None:
    from transmission_rpc.torrent import Status
    s = Status("checking")
    assert s.checking
    assert not s.stopped
    s = Status("check pending")
    assert s.check_pending
    s = Status("downloading")
    assert s.downloading
    s = Status("download pending")
    assert s.download_pending
    s = Status("seeding")
    assert s.seeding
    s = Status("seed pending")
    assert s.seed_pending

def test_torrent_misc_properties() -> None:
    fields = {
        "id": 1,
        "seedIdleMode": 0, # global
        "status": 4, # downloading
    }
    t = Torrent(fields=fields)
    assert t.seed_idle_mode.value == 0
    assert t._status_str == "downloading"
