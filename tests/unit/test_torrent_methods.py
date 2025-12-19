from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from transmission_rpc.constants import IdleMode, Priority, RatioLimitMode
from transmission_rpc.torrent import FileStat, Peer, PeersFrom, Status, Torrent, Tracker, TrackerStats


@pytest.fixture
def torrent_fields() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "test",
        "hashString": "0000000000000000000000000000000000000000",
        "status": 0,
        "bandwidthPriority": 0,
        "comment": "comment",
        "corruptEver": 0,
        "creator": "creator",
        "dateCreated": 0,
        "desiredAvailable": 0,
        "downloadDir": "/tmp",
        "downloadedEver": 0,
        "downloadLimit": 0,
        "downloadLimited": False,
        "editDate": 0,
        "error": 0,
        "errorString": "",
        "eta": -1,
        "etaIdle": -1,
        "file-count": 1,
        "files": [
            {"length": 100, "name": "file1", "bytesCompleted": 50, "begin_piece": 0, "end_piece": 1},
        ],
        "fileStats": [{"bytesCompleted": 50, "wanted": True, "priority": 0}],
        "group": "",
        "haveUnchecked": 0,
        "haveValid": 0,
        "honorsSessionLimits": False,
        "isFinished": False,
        "isPrivate": False,
        "isStalled": False,
        "labels": [],
        "leftUntilDone": 50,
        "magnetLink": "magnet:?",
        "manualAnnounceTime": 0,
        "maxConnectedPeers": 0,
        "metadataPercentComplete": 1.0,
        "peer-limit": 0,
        "peers": [],
        "peersConnected": 0,
        "peersFrom": {
            "fromCache": 0,
            "fromDht": 0,
            "fromIncoming": 0,
            "fromLpd": 0,
            "fromLtep": 0,
            "fromPex": 0,
            "fromTracker": 0,
        },
        "peersGettingFromUs": 0,
        "peersSendingToUs": 0,
        "percentComplete": 0.5,
        "percentDone": 0.5,
        "pieces": "AAAA",
        "pieceCount": 1,
        "pieceSize": 100,
        "priorities": [0],
        "primary-mime-type": "",
        "queuePosition": 0,
        "rateDownload": 0,
        "rateUpload": 0,
        "recheckProgress": 0.0,
        "secondsDownloading": 0,
        "secondsSeeding": 0,
        "seedIdleLimit": 0,
        "seedIdleMode": 0,
        "sizeWhenDone": 100,
        "trackers": [],
        "trackerList": "",
        "trackerStats": [],
        "totalSize": 100,
        "torrentFile": "/tmp/test.torrent",
        "uploadedEver": 0,
        "uploadLimit": 0,
        "uploadLimited": False,
        "uploadRatio": 0.0,
        "wanted": [1],
        "webseeds": [],
        "webseedsSendingToUs": 0,
        "activityDate": 0,
        "addedDate": 0,
        "startDate": 0,
        "doneDate": 0,
        "seedRatioLimit": 0.0,
        "seedRatioMode": 0,
        "sequential_download": False,
    }


def test_torrent_properties(torrent_fields: dict[str, Any]) -> None:
    t = Torrent(fields=torrent_fields)
    assert t.id == 1
    assert t.name == "test"
    assert t.hash_string == "0000000000000000000000000000000000000000"
    assert t.info_hash == t.hash_string
    with pytest.warns(DeprecationWarning, match="this is a typo"):
        assert t.into_hash == t.hash_string

    assert t.bandwidth_priority == Priority.Normal
    assert t.comment == "comment"
    assert t.corrupt_ever == 0
    assert t.creator == "creator"
    assert t.desired_available == 0
    assert t.download_dir == "/tmp"  # noqa: S108
    assert t.downloaded_ever == 0
    assert t.download_limit == 0
    assert t.download_limited is False
    assert t.edit_date == datetime.fromtimestamp(0, timezone.utc)
    assert t.error == 0
    assert t.error_string == ""
    assert t.eta is None
    assert t.eta_idle is None
    assert t.file_count == 1
    assert len(t.get_files()) == 1
    assert len(t.file_stats) == 1
    assert t.group == ""
    assert t.have_unchecked == 0
    assert t.have_valid == 0
    assert t.honors_session_limits is False
    assert t.is_finished is False
    assert t.is_private is False
    assert t.is_stalled is False
    assert t.labels == []
    assert t.left_until_done == 50
    assert t.magnet_link == "magnet:?"
    assert t.manual_announce_time == datetime.fromtimestamp(0, timezone.utc)
    assert t.max_connected_peers == 0
    assert t.metadata_percent_complete == 1.0
    assert t.peer_limit == 0
    assert t.peers == []
    assert t.peers_connected == 0
    assert isinstance(t.peers_from, PeersFrom)
    assert t.peers_getting_from_us == 0
    assert t.peers_sending_to_us == 0
    assert t.percent_complete == 0.5
    assert t.percent_done == 0.5
    assert t.piece_count == 1
    assert t.piece_size == 100
    assert t.primary_mime_type == ""
    assert t.queue_position == 0
    assert t.rate_download == 0
    assert t.rate_upload == 0
    assert t.recheck_progress == 0.0
    assert t.seconds_downloading == 0
    assert t.seconds_seeding == 0
    assert t.seed_idle_limit == 0
    assert t.seed_idle_mode == IdleMode.Global
    assert t.size_when_done == 100
    assert t.trackers == []
    assert t.tracker_list == []
    assert t.tracker_stats == []
    assert t.total_size == 100
    assert t.torrent_file == "/tmp/test.torrent"  # noqa: S108
    assert t.uploaded_ever == 0
    assert t.upload_limit == 0
    assert t.upload_limited is False
    assert t.upload_ratio == 0.0
    assert t.wanted == [1]
    assert t.webseeds == []
    assert t.webseeds_sending_to_us == 0
    assert t.status.stopped
    assert t.progress == 50.0
    assert t.ratio == 0.0
    assert t.activity_date == datetime.fromtimestamp(0, timezone.utc)
    assert t.added_date == datetime.fromtimestamp(0, timezone.utc)
    assert t.start_date == datetime.fromtimestamp(0, timezone.utc)
    assert t.done_date is None
    assert t.format_eta() == "not available"
    assert t.priority == Priority.Normal
    assert t.seed_ratio_limit == 0.0
    assert t.seed_ratio_mode == RatioLimitMode.Global
    assert t.sequential_download is False
    assert repr(t).startswith("<transmission_rpc.Torrent")
    assert str(t).startswith("<transmission_rpc.Torrent")


def test_torrent_status_properties(torrent_fields: dict[str, Any]) -> None:
    for code, name in [
        (0, "stopped"),
        (1, "check pending"),
        (2, "checking"),
        (3, "download pending"),
        (4, "downloading"),
        (5, "seed pending"),
        (6, "seeding"),
    ]:
        torrent_fields["status"] = code
        t = Torrent(fields=torrent_fields)
        assert t._status == code  # noqa: SLF001
        assert t._status_str == name  # noqa: SLF001
        assert getattr(t, name.replace(" ", "_"))


def test_torrent_eta_valid(torrent_fields: dict[str, Any]) -> None:
    torrent_fields["eta"] = 3600
    t = Torrent(fields=torrent_fields)
    assert t.eta == timedelta(seconds=3600)
    # The actual format depends on format_timedelta implementation, adjusting to match observation
    # Observation: '0 01:00:00'
    assert t.format_eta() == "0 01:00:00"


def test_torrent_eta_unknown(torrent_fields: dict[str, Any]) -> None:
    torrent_fields["eta"] = -2
    t = Torrent(fields=torrent_fields)
    assert t.format_eta() == "unknown"


def test_torrent_eta_idle_valid(torrent_fields: dict[str, Any]) -> None:
    torrent_fields["etaIdle"] = 3600
    t = Torrent(fields=torrent_fields)
    assert t.eta_idle == timedelta(seconds=3600)


def test_torrent_done_date_valid(torrent_fields: dict[str, Any]) -> None:
    torrent_fields["doneDate"] = 1000
    t = Torrent(fields=torrent_fields)
    assert t.done_date == datetime.fromtimestamp(1000, timezone.utc)


def test_torrent_progress_calc(torrent_fields: dict[str, Any]) -> None:
    del torrent_fields["percentDone"]
    t = Torrent(fields=torrent_fields)
    # sizeWhenDone=100, leftUntilDone=50 -> 50%
    assert t.progress == 50.0


def test_torrent_progress_zero_division(torrent_fields: dict[str, Any]) -> None:
    del torrent_fields["percentDone"]
    torrent_fields["sizeWhenDone"] = 0
    t = Torrent(fields=torrent_fields)
    assert t.progress == 0.0


def test_torrent_available_calc(torrent_fields: dict[str, Any]) -> None:
    # total_size=100
    # bytesCompleted=50 (in fileStats)
    # desiredAvailable=0
    # available = (0 + 50) / 100 * 100 = 50.0
    t = Torrent(fields=torrent_fields)
    assert t.available == 50.0


def test_torrent_available_zero(torrent_fields: dict[str, Any]) -> None:
    torrent_fields["totalSize"] = 0
    t = Torrent(fields=torrent_fields)
    assert t.available == 0.0


def test_peer_properties() -> None:
    data: dict[str, Any] = {
        "address": "1.2.3.4",
        "clientName": "client",
        "clientIsChoked": True,
        "clientIsInterested": False,
        "flagStr": "flag",
        "isDownloadingFrom": False,
        "isEncrypted": True,
        "isIncoming": False,
        "isUploadingTo": False,
        "isUTP": False,
        "peerIsChoked": True,
        "peerIsInterested": False,
        "port": 1234,
        "progress": 0.5,
        "rateToClient": 0.0,
        "rateToPeer": 0.0,
    }
    p = Peer(fields=data)
    assert p.address == "1.2.3.4"
    assert p.client_name == "client"
    assert p.client_is_choked is True
    assert p.client_is_interested is False
    assert p.flag_str == "flag"
    assert p.is_downloading_from is False
    assert p.is_encrypted is True
    assert p.is_incoming is False
    assert p.is_uploading_to is False
    assert p.is_utp is False
    assert p.peer_is_choked is True
    assert p.peer_is_interested is False
    assert p.port == 1234
    assert p.progress == 0.5
    assert p.rate_to_client == 0.0
    assert p.rate_to_peer == 0.0


def test_peers_from_properties() -> None:
    data: dict[str, Any] = {
        "fromCache": 1,
        "fromDht": 2,
        "fromIncoming": 3,
        "fromLpd": 4,
        "fromLtep": 5,
        "fromPex": 6,
        "fromTracker": 7,
    }
    pf = PeersFrom(fields=data)
    assert pf.from_cache == 1
    assert pf.from_dht == 2
    assert pf.from_incoming == 3
    assert pf.from_lpd == 4
    assert pf.from_ltep == 5
    assert pf.from_pex == 6
    assert pf.from_tracker == 7


def test_file_stat_properties() -> None:
    data: dict[str, Any] = {"bytesCompleted": 100, "wanted": True, "priority": 1}
    fs = FileStat(fields=data)
    assert fs.bytesCompleted == 100
    assert fs.wanted is True
    assert fs.priority == 1


def test_tracker_properties() -> None:
    data: dict[str, Any] = {"id": 1, "announce": "url", "scrape": "scrape", "tier": 1}
    t = Tracker(fields=data)
    assert t.id == 1
    assert t.announce == "url"
    assert t.scrape == "scrape"
    assert t.tier == 1


def test_tracker_stats_properties() -> None:
    data: dict[str, Any] = {
        "id": 1,
        "announceState": 1,
        "announce": "url",
        "downloadCount": 10,
        "hasAnnounced": True,
        "hasScraped": True,
        "host": "host",
        "isBackup": False,
        "lastAnnouncePeerCount": 5,
        "lastAnnounceResult": "ok",
        "lastAnnounceStartTime": 0,
        "lastAnnounceSucceeded": True,
        "lastAnnounceTime": 0,
        "lastAnnounceTimedOut": False,
        "lastScrapeResult": "ok",
        "lastScrapeStartTime": 0,
        "lastScrapeSucceeded": True,
        "lastScrapeTime": 0,
        "lastScrapeTimedOut": False,
        "leecherCount": 2,
        "nextAnnounceTime": 0,
        "nextScrapeTime": 0,
        "scrapeState": 1,
        "scrape": "scrape",
        "seederCount": 3,
        "sitename": "site",
        "tier": 1,
    }
    ts = TrackerStats(fields=data)
    assert ts.id == 1
    assert ts.announce_state == 1
    assert ts.announce == "url"
    assert ts.download_count == 10
    assert ts.has_announced is True
    assert ts.has_scraped is True
    assert ts.host == "host"
    assert ts.is_backup is False
    assert ts.last_announce_peer_count == 5
    assert ts.last_announce_result == "ok"
    assert ts.last_announce_start_time == 0
    assert ts.last_announce_succeeded is True
    assert ts.last_announce_time == 0
    assert ts.last_announce_timed_out is False
    assert ts.last_scrape_result == "ok"
    assert ts.last_scrape_start_time == 0
    assert ts.last_scrape_succeeded is True
    assert ts.last_scrape_time == 0
    assert ts.last_scrape_timed_out is False
    assert ts.leecher_count == 2
    assert ts.next_announce_time == 0
    assert ts.next_scrape_time == 0
    assert ts.scrape_state == 1
    assert ts.scrape == "scrape"
    assert ts.seeder_count == 3
    assert ts.site_name == "site"
    assert ts.tier == 1


def test_status_str() -> None:
    assert str(Status.STOPPED) == "stopped"


def test_torrent_queue_position(torrent_fields: dict[str, Any]) -> None:
    t = Torrent(fields=torrent_fields)
    assert t.queue_position == 0
