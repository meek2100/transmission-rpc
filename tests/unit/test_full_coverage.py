# ruff: noqa: SLF001, S108
import io
import json
import pathlib
from unittest import mock

import pytest

from transmission_rpc.client import Client, Timeout, TransmissionError
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent


def test_http_unix_init():
    """Cover initialization of http+unix protocol"""
    with mock.patch("transmission_rpc.client.UnixHTTPConnectionPool") as mock_pool:
        # Patch the method on the class directly to ensure it catches all instances
        with mock.patch.object(Client, "get_session", autospec=True):
            c = Client(protocol="http+unix", host="/tmp/test", path="/transmission/")
            assert c._url == "http+unix://localhost:9091/transmission/rpc"

def test_json_decode_error():
    """Cover JSON decode error handling in _request"""
    # Patch get_session so init doesn't make network calls
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Mock _http_query to return non-json string
        # We need to mock the instance method on the created instance 'c'
        c._http_query = mock.Mock(return_value="not json")
        # We need a logger mock
        c.logger = mock.Mock()

        # Now call _request
        with pytest.raises(TransmissionError) as excinfo:
            c._request("method")
        assert "failed to parse response as json" in str(excinfo.value)
        c.logger.exception.assert_called()

def test_import_error_version():
    """Cover the ImportError block for version retrieval"""
    # We need to force a reload of the module to trigger the top-level try/except
    import importlib

    import transmission_rpc.client

    # Mock importlib.metadata.version to raise ImportError
    with mock.patch("importlib.metadata.version", side_effect=ImportError):
        # Reload the module
        importlib.reload(transmission_rpc.client)
        assert transmission_rpc.client.__version__ == "develop"

    # Restore normal version
    importlib.reload(transmission_rpc.client)

def test_deprecated_client_properties():
    """Cover deprecated properties"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Manually set private attributes that are usually set in init/get_session
        c._Client__semver_version = "1.0.0"
        c._Client__protocol_version = 15

        # Access deprecated properties
        with pytest.warns(DeprecationWarning):
            assert c.semver_version == "1.0.0"
        with pytest.warns(DeprecationWarning):
            assert c.rpc_version == 15
        with pytest.warns(DeprecationWarning):
            assert c.url == c._url
        with pytest.warns(DeprecationWarning):
            assert c.session_id == "0"
        with pytest.warns(DeprecationWarning):
            assert c.server_version == "(unknown)"
        with pytest.warns(DeprecationWarning):
            assert c.torrent_get_arguments == c._Client__torrent_get_arguments
        with pytest.warns(DeprecationWarning):
            assert c.raw_session == {}

def test_file_scheme_error():
    """Cover usage of file:// scheme error"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        with pytest.raises(ValueError, match="support for `file://` URL has been removed"):
            c.add_torrent("file:///tmp/test.torrent")

def test_change_torrent_warnings():
    """Cover warnings for new RPC features"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # Mock internal request method
        c._request = mock.Mock()
        c.logger = mock.Mock()
        # Mock _rpc_version_warning to verify calls
        c._rpc_version_warning = mock.Mock()

        # Test labels warning (v16)
        c.change_torrent(ids=1, labels=["a"])
        c._rpc_version_warning.assert_any_call(16)

        # Test group warning (v17)
        c.change_torrent(ids=1, group="g")
        c._rpc_version_warning.assert_any_call(17)

        # Test tracker_list warning (v17)
        c.change_torrent(ids=1, tracker_list=[["a"]])
        c._rpc_version_warning.assert_any_call(17)

def test_session_default_trackers():
    """Cover session default_trackers property"""
    s = Session(fields={"default-trackers": "t1\nt2"})
    assert s.default_trackers == ["t1", "t2"]

    s2 = Session(fields={})
    assert s2.default_trackers is None

def test_torrent_methods_and_props():
    """Cover misc torrent methods and properties"""
    fields = {
        "id": 1,
        "name": "test",
        "hashString": "hash",
        "file-count": 5,
        "primary-mime-type": "text/plain",
        "files": [{"length": 100, "name": "f1", "bytesCompleted": 100}],
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "eta": -1,
        "percentDone": 0.5,
        "sizeWhenDone": 100,
        "leftUntilDone": 50,
        "uploadRatio": 1.0,
        "status": 0,
        # Add missing fields to avoid KeyErrors if accessed
        "bandwidthPriority": 0,
        "corruptEver": 0,
        "creator": "",
        "desiredAvailable": 0,
        "downloadDir": "",
        "downloadedEver": 0,
        "downloadLimit": 0,
        "downloadLimited": False,
        "editDate": 0,
        "error": 0,
        "errorString": "",
        "etaIdle": 0,
        "haveUnchecked": 0,
        "haveValid": 0,
        "honorsSessionLimits": False,
        "isFinished": False,
        "isPrivate": False,
        "isStalled": False,
        "labels": [],
        "magnetLink": "",
        "manualAnnounceTime": 0,
        "maxConnectedPeers": 0,
        "metadataPercentComplete": 0.0,
        "peer-limit": 0,
        "peers": [],
        "peersConnected": 0,
        "peersFrom": {},
        "peersGettingFromUs": 0,
        "peersSendingToUs": 0,
        "percentComplete": 0.0,
        "pieces": "",
        "pieceCount": 0,
        "pieceSize": 0,
        "queuePosition": 0,
        "rateDownload": 0,
        "rateUpload": 0,
        "recheckProgress": 0.0,
        "secondsDownloading": 0,
        "secondsSeeding": 0,
        "seedIdleLimit": 0,
        "seedIdleMode": 0,
        "seedRatioLimit": 0.0,
        "seedRatioMode": 0,
        "sequential_download": False,
        "totalSize": 100,
        "torrentFile": "",
        "uploadedEver": 0,
        "uploadLimit": 0,
        "uploadLimited": False,
        # "wanted": [],
        "webseeds": [],
        "webseedsSendingToUs": 0,
        "activityDate": 0,
        "addedDate": 0,
        "startDate": 0,
        "doneDate": 0,
        "trackers": [],
        "trackerList": "",
        "trackerStats": [],
        # "priorities" is INTENTIONALLY OMITTED to test default branch
    }

    t = Torrent(fields=fields)

    # available
    # bytes_done = 100
    # bytes_avail = 0 + 100 = 100
    # ratio = 100 / 100 = 1.0 => 100.0
    assert t.available == 100.0

    # __str__ and __repr__
    assert str(t) == "<transmission_rpc.Torrent 'test'>"
    assert repr(t) == "<transmission_rpc.Torrent hashString='hash'>"

    # Properties
    assert t.file_count == 5
    assert t.primary_mime_type == "text/plain"

    # format_eta edge cases
    assert t.format_eta() == "not available"
    t.fields["eta"] = -2
    assert t.format_eta() == "unknown"
    t.fields["eta"] = 3600
    assert t.format_eta() == "0 01:00:00"

    # Deprecated into_hash
    with pytest.warns(DeprecationWarning):
        assert t.into_hash == "hash"

    # get_files defaults (when priorities/wanted are missing)
    files = t.get_files()
    assert len(files) == 1
    assert files[0].priority is None
    assert files[0].selected is None

    # pieces
    assert t.pieces is not None

    # Progress ZeroDivisionError check
    # Force percentDone missing to trigger calculation
    del t.fields["percentDone"]
    t.fields["sizeWhenDone"] = 0
    t.fields["leftUntilDone"] = 0
    # Should catch ZeroDivisionError and return 0.0
    assert t.progress == 0.0

    # Init missing id
    with pytest.raises(ValueError, match="requires field 'id'"):
        Torrent(fields={})

def test_groups_coverage():
    """Cover set_group and get_groups which are skipped on older servers"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        # We need to mock _request to return something valid
        c._request = mock.Mock(return_value={"group": [{"name": "test_g"}]})

        # Test set_group
        c.set_group("test_g")
        c._request.assert_called_with(mock.ANY, {"name": "test_g"}, timeout=None)

        # Test get_groups
        groups = c.get_groups()
        assert "test_g" in groups

        # Test get_group
        g = c.get_group("test_g")
        assert g.name == "test_g"

        # Test get_group missing
        c._request.return_value = {"group": []}
        assert c.get_group("missing") is None

        # Test get_groups with list
        c.get_groups(["test_g"])
        c._request.assert_called_with(mock.ANY, {"group": ["test_g"]}, timeout=None)

def test_remove_unset_value():
    from transmission_rpc.client import remove_unset_value
    assert remove_unset_value({"a": 1, "b": None}) == {"a": 1}

def test_single_str_as_list():
    from transmission_rpc.client import _single_str_as_list
    assert _single_str_as_list(None) is None
    assert _single_str_as_list("a") == ["a"]
    assert _single_str_as_list(["a"]) == ["a"]

def test_timeout_property():
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client(timeout=10)
        assert isinstance(c.timeout, Timeout)

        c.timeout = Timeout(20)
        assert c.timeout.total == 20

        with pytest.raises(TypeError):
            c.timeout = 10

        del c.timeout
        assert c.timeout.total == 30.0 # Default

def test_ensure_location_str():
    # Only test the Path branch as str is trivial
    from transmission_rpc.client import ensure_location_str
    p = pathlib.Path("/tmp")
    assert ensure_location_str(p) == str(p)

def test_client_init_variations():
    """Cover Client init branches"""
    with mock.patch.object(Client, "get_session", autospec=True):
        # timeout=None
        c = Client(timeout=None)
        assert c.timeout is None

        # timeout=Timeout object
        t = Timeout(10)
        c = Client(timeout=t)
        assert c.timeout is t

        # path fix
        c = Client(path="/transmission/")
        assert c._path == "/transmission/rpc"

        # Auth
        c = Client(username="u", password="p")

        # HTTPS
        with mock.patch("transmission_rpc.client.urllib3.HTTPSConnectionPool") as mock_https:
            c = Client(protocol="https")
            mock_https.assert_called()

def test_ensure_location_str_error():
    """Cover ensure_location_str relative path error"""
    from transmission_rpc.client import ensure_location_str
    p = pathlib.Path("relative/path")
    with pytest.raises(ValueError, match="using relative `pathlib.Path`"):
        ensure_location_str(p)

def test_request_errors():
    """Cover _request type checking and logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()

        # Method check
        with pytest.raises(TypeError, match="request takes method as string"):
            c._request(method=123) # type: ignore

        # Arguments check
        with pytest.raises(TypeError, match="request takes arguments should be dict"):
            c._request(method="m", arguments="not dict") # type: ignore

        # Require ids
        with pytest.raises(ValueError, match="request require ids"):
            c._request(method="m", require_ids=True)

def test_request_response_logic():
    """Cover response parsing logic"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c.logger = mock.Mock()
        # Enable debug to cover logging
        c.logger.isEnabledFor.return_value = True

        # Mock _http_query
        # 1. Missing result
        c._http_query = mock.Mock(return_value=json.dumps({"arguments": {}}))
        with pytest.raises(TransmissionError, match="missing without result"):
            c._request("method")

        c.logger.debug.assert_called()

def test_more_client_methods():
    """Cover remaining client methods"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()

        # start_all bypass_queue
        c._request.return_value = {"torrents": []}
        c.start_all(bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"

        # stop_torrent
        c.stop_torrent(ids=1)

        # reannounce_torrent
        c.reannounce_torrent(ids=1)

        # blocklist_update
        c._request.return_value = {"blocklist-size": 10}
        assert c.blocklist_update() == 10

        # session_close
        c.session_close()

        # Context manager
        c.close = mock.Mock()
        with c:
            pass
        c.close.assert_called()

def test_add_torrent_args():
    """Cover add_torrent args"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})

        # labels, sequential_download, bandwidthPriority
        c.add_torrent("magnet:?xt=urn:btih:a", labels=["l"], sequential_download=True, bandwidthPriority=1)

def test_even_more_coverage():
    """Cover remaining lines"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()

        # set_session invalid encryption
        with pytest.raises(ValueError, match="Invalid encryption value"):
            c.set_session(encryption="invalid") # type: ignore

        # start_torrent bypass_queue
        c.start_torrent(ids=1, bypass_queue=True)
        assert c._request.call_args[0][0] == "torrent-start-now"

        # get_torrents with arguments
        c._request.return_value = {"torrents": []}
        c.get_torrents(ids=1, arguments=["name"])
        args = c._request.call_args[0][1]["fields"]
        assert "name" in args and "id" in args

        # get_recently_active_torrents with arguments
        c._request.return_value = {"torrents": [], "removed": []}
        c.get_recently_active_torrents(arguments=["name"])
        args = c._request.call_args[0][1]["fields"]
        assert "name" in args

        # free_space success
        c._request.return_value = {"path": "/tmp", "size-bytes": 100}
        assert c.free_space("/tmp") == 100

        # free_space fail
        c._request.return_value = {"path": "/other", "size-bytes": 0}
        assert c.free_space("/tmp") is None

def test_add_torrent_types():
    """Cover add_torrent with different input types"""

    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock(return_value={"torrent-added": {"id": 1, "name": "n", "hashString": "h"}})

        # bytes
        c.add_torrent(b"torrent content")
        assert "metainfo" in c._request.call_args[0][1]

        # file-like
        f = io.BytesIO(b"torrent content")
        c.add_torrent(f)
        assert "metainfo" in c._request.call_args[0][1]

        # Path (local file)
        # We need to mock path reading
        p = pathlib.Path("test.torrent")
        with mock.patch("pathlib.Path.read_bytes", return_value=b"content"):
             c.add_torrent(p)
        assert "metainfo" in c._request.call_args[0][1]

def test_final_straw():
    """Cover the last few lines"""
    with mock.patch.object(Client, "get_session", autospec=True):
        c = Client()
        c._request = mock.Mock()

        # 489: empty metadata
        with pytest.raises(ValueError, match="Torrent metadata is empty"):
            c.add_torrent(b"")

        # 1255: _try_read_torrent returns None for unknown type
        # We pass an object that is not str/Path/bytes/read
        obj = object()
        # It returns None, so code proceeds to: kwargs["filename"] = obj
        # Then calls _request.
        c._request.return_value = {"torrent-added": {"id": 1}}
        c.add_torrent(obj) # type: ignore

        # start_all bypass_queue with torrents to fully exercise logic
        c._request.side_effect = [
            {"torrents": [{"id": 1, "hashString": "h", "queuePosition": 0}]}, # get_torrents
            {} # start
        ]
        c.start_all(bypass_queue=True)
        # Check second call argument
        assert c._request.call_args_list[-1][0][0] == "torrent-start-now"

    # Use a new client to test _request logic because we need the real _request to run
    # Client.get_session is already patched by the outer context if we are not careful
    # But here we are outside the with block of c

    with mock.patch.object(Client, "get_session", autospec=True):
        c2 = Client()
        c2.logger = mock.Mock()

        # 1. SessionStats fallback (358)
        c2._http_query = mock.Mock(return_value=json.dumps({
            "result": "success",
            "arguments": {"activeTorrentCount": 1}
        }))
        stats = c2.session_stats()
        assert stats.active_torrent_count == 1

        # 2. TorrentAdd logic (338)
        c2._http_query.return_value = json.dumps({
            "result": "success",
            "arguments": {"torrent-added": {"id": 1, "name": "n", "hashString": "h"}}
        })
        # add_torrent calls _request. We pass 'magnet' so it doesn't try to read file.
        t = c2.add_torrent("magnet:?xt=urn:btih:h")
        assert t.id == 1

        # 3. get_torrent finding torrent (593-594)
        c2._http_query.return_value = json.dumps({
            "result": "success",
            "arguments": {"torrents": [{"id": 1, "name": "n", "hashString": "h"}]}
        })
        t = c2.get_torrent(1)
        assert t.id == 1
