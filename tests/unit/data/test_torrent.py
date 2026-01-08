# ruff: noqa: SLF001
import calendar
import contextlib
import datetime
import time
from typing import Any

import pytest

import transmission_rpc
import transmission_rpc.constants
import transmission_rpc.utils
from transmission_rpc.torrent import FileStat, Status, Torrent, get_status


def check_properties(cls: type, obj: Any) -> None:
    for prop in dir(cls):
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)


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


def test_torrent_status_properties() -> None:
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
        "seedIdleMode": 0,  # global
        "status": 4,  # downloading
    }
    t = Torrent(fields=fields)
    assert t.seed_idle_mode.value == 0
    assert t._status_str == "downloading"


def test_torrent_methods_and_props() -> None:
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
    with pytest.warns(DeprecationWarning, match="typo"):
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


def test_torrent_properties_access() -> None:
    t = Torrent(fields={"id": 1})
    check_properties(Torrent, t)


def test_file_stat_properties_access() -> None:
    f = FileStat(fields={})
    check_properties(FileStat, f)


def test_status_properties_full() -> None:
    s = Status("stopped")
    assert s.stopped is True
    assert s.check_pending is False
    assert str(s) == "stopped"

    check_properties(Status, s)


def test_torrent_rich_fields() -> None:
    fields = {
        "id": 1,
        "eta": -1,
        "etaIdle": -1,
        "pieces": "AA==",  # base64 for 0x00
        "fileStats": [],
        "files": [],
        "priorities": [],
        "wanted": [],
        "peers": [],
        "trackers": [],
        "trackerStats": [],
        "trackerList": "",
        "status": 0,
        "activityDate": 0,
        "addedDate": 0,
        "startDate": 0,
        "doneDate": 0,
    }
    t = Torrent(fields=fields)
    assert t.format_eta() == "not available"
    assert t.eta is None
    assert t.eta_idle is None
    assert t.done_date is None

    fields["eta"] = -2
    t = Torrent(fields=fields)
    assert t.format_eta() == "unknown"

    fields["eta"] = 3600
    fields["etaIdle"] = 60
    fields["doneDate"] = 1000000000
    t = Torrent(fields=fields)
    assert str(t.eta) == "1:00:00"
    assert str(t.eta_idle) == "0:01:00"
    assert t.done_date is not None


def test_status_unknown() -> None:
    assert get_status(999) == "unknown status 999"


def assert_property_exception(exception, ob, prop):
    """Helper to assert that accessing a property raises a specific exception."""
    with pytest.raises(exception):
        getattr(ob, prop)


def test_non_active():
    """
    Verify that a Torrent object correctly handles the 'activityDate' field being 0 (non-active).
    """
    data = {
        "id": 1,
        "activityDate": 0,
    }

    torrent = transmission_rpc.Torrent(fields=data)
    assert torrent.activity_date


def test_attributes():
    """
    Verify that Torrent attributes are correctly populated from the 'fields' dictionary
    and that accessing missing fields raises KeyError.
    """
    torrent = transmission_rpc.Torrent(fields={"id": 42})
    assert torrent.id == 42
    assert_property_exception(KeyError, torrent, "status")
    assert_property_exception(KeyError, torrent, "progress")
    assert_property_exception(KeyError, torrent, "ratio")
    assert_property_exception(KeyError, torrent, "eta")
    assert_property_exception(KeyError, torrent, "activity_date")
    assert_property_exception(KeyError, torrent, "added_date")
    assert_property_exception(KeyError, torrent, "start_date")
    assert_property_exception(KeyError, torrent, "done_date")

    with pytest.raises(KeyError):
        torrent.format_eta()
    with pytest.raises(KeyError):
        torrent.get_files()

    data = {
        "id": 1,
        "status": 4,
        "sizeWhenDone": 1000,
        "leftUntilDone": 500,
        "uploadedEver": 1000,
        "downloadedEver": 2000,
        "uploadRatio": 0.5,
        "eta": 3600,
        "percentDone": 0.5,
        "activityDate": calendar.timegm((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": calendar.timegm((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": calendar.timegm((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": calendar.timegm((2008, 12, 11, 10, 0, 15, 0, 0, -1)),
    }

    torrent = transmission_rpc.Torrent(fields=data)
    assert torrent.id == 1
    assert torrent.left_until_done == 500
    assert torrent.status == "downloading"
    assert torrent.status.downloading
    assert torrent.progress == 50.0
    assert torrent.ratio == 0.5
    assert torrent.eta == datetime.timedelta(seconds=3600)
    assert torrent.activity_date == datetime.datetime(2008, 12, 11, 11, 15, 30, tzinfo=datetime.timezone.utc)
    assert torrent.added_date == datetime.datetime(2008, 12, 11, 8, 5, 10, tzinfo=datetime.timezone.utc)
    assert torrent.start_date == datetime.datetime(2008, 12, 11, 9, 10, 5, tzinfo=datetime.timezone.utc)
    assert torrent.done_date == datetime.datetime(2008, 12, 11, 10, 0, 15, tzinfo=datetime.timezone.utc)

    assert torrent.format_eta() == transmission_rpc.utils.format_timedelta(torrent.eta)

    data = {
        "id": 1,
        "status": 4,
        "sizeWhenDone": 1000,
        "leftUntilDone": 500,
        "uploadedEver": 1000,
        "downloadedEver": 2000,
        "uploadRatio": 0.5,
        "eta": 3600,
        "activityDate": time.mktime((2008, 12, 11, 11, 15, 30, 0, 0, -1)),
        "addedDate": time.mktime((2008, 12, 11, 8, 5, 10, 0, 0, -1)),
        "startDate": time.mktime((2008, 12, 11, 9, 10, 5, 0, 0, -1)),
        "doneDate": 0,
    }

    torrent = transmission_rpc.Torrent(fields=data)
    assert torrent.done_date is None
