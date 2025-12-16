import pytest
from transmission_rpc.constants import Priority
from transmission_rpc.session import Session, SessionStats
from transmission_rpc.torrent import FileStat, PeersFrom, Status, Torrent, Tracker, TrackerStats
from transmission_rpc.types import BitMap, Container, Group, PortTestResult


def test_container_init():
    c = Container(fields={"key": "value"})
    assert c.fields["key"] == "value"


def test_container_getattr():
    c = Container(fields={"key": "value"})
    assert c.get("key") == "value"


def test_container_repr():
    c = Container(fields={"key": "value"})
    assert isinstance(repr(c), str)
    assert "key" in repr(c)


def test_group_init():
    g = Group(fields={"name": "test"})
    assert g.name == "test"


def test_group_properties():
    data = {
        "name": "group",
        "honorsSessionLimits": True,
        "speed-limit-down-enabled": True,
        "speed-limit-down": 100,
        "speed-limit-up-enabled": True,
        "speed-limit-up": 100,
    }
    g = Group(fields=data)
    assert g.name == "group"
    assert g.honors_session_limits is True
    assert g.speed_limit_down_enabled is True
    assert g.speed_limit_down == 100
    assert g.speed_limit_up_enabled is True
    assert g.speed_limit_up == 100


def test_file_stat():
    data = {"bytesCompleted": 100, "wanted": True, "priority": 1}
    fs = FileStat(fields=data)
    assert fs.bytesCompleted == 100
    assert fs.wanted is True
    assert fs.priority == 1


def test_tracker():
    data = {"announce": "url", "id": 1, "scrape": "url", "tier": 1}
    t = Tracker(fields=data)
    assert t.announce == "url"
    assert t.id == 1
    assert t.scrape == "url"
    assert t.tier == 1


def test_tracker_stats():
    data = {
        "announce": "url",
        "announceState": 1,
        "downloadCount": 1,
        "hasAnnounced": True,
        "hasScraped": True,
        "host": "host",
        "id": 1,
        "isBackup": False,
        "lastAnnouncePeerCount": 1,
        "lastAnnounceResult": "success",
        "lastAnnounceStartTime": 100,
        "lastAnnounceSucceeded": True,
        "lastAnnounceTime": 100,
        "lastAnnounceTimedOut": False,
        "lastScrapeResult": "success",
        "lastScrapeStartTime": 100,
        "lastScrapeSucceeded": True,
        "lastScrapeTime": 100,
        "lastScrapeTimedOut": False,
        "leecherCount": 1,
        "nextAnnounceTime": 100,
        "nextScrapeTime": 100,
        "scrape": "url",
        "scrapeState": 1,
        "seederCount": 1,
        "tier": 1,
        "sitename": "site",
    }
    t = TrackerStats(fields=data)
    assert t.announce == "url"
    assert t.announce_state == 1
    assert t.download_count == 1
    assert t.has_announced is True
    assert t.has_scraped is True
    assert t.host == "host"
    assert t.id == 1
    assert t.is_backup is False
    assert t.last_announce_peer_count == 1
    assert t.last_announce_result == "success"
    assert t.last_announce_start_time == 100
    assert t.last_announce_succeeded is True
    assert t.last_announce_time == 100
    assert t.last_announce_timed_out is False
    assert t.last_scrape_result == "success"
    assert t.last_scrape_start_time == 100
    assert t.last_scrape_succeeded is True
    assert t.last_scrape_time == 100
    assert t.last_scrape_timed_out is False
    assert t.leecher_count == 1
    assert t.next_announce_time == 100
    assert t.next_scrape_time == 100
    assert t.scrape == "url"
    assert t.scrape_state == 1
    assert t.seeder_count == 1
    assert t.tier == 1
    assert t.site_name == "site"


def test_peers_from():
    data = {
        "fromCache": 1,
        "fromDht": 2,
        "fromIncoming": 3,
        "fromLpd": 4,
        "fromLtep": 5,
        "fromPex": 6,
        "fromTracker": 7,
    }
    p = PeersFrom(fields=data)
    assert p.from_cache == 1
    assert p.from_dht == 2
    assert p.from_incoming == 3
    assert p.from_lpd == 4
    assert p.from_ltep == 5
    assert p.from_pex == 6
    assert p.from_tracker == 7


def test_port_test_result():
    data = {"port-is-open": True, "ip_protocol": "ipv4"}
    r = PortTestResult(fields=data)
    assert r.port_is_open is True
    assert r.ip_protocol == "ipv4"


def test_bitmap():
    # 1000 0000 -> 128
    b = BitMap(b"\x80")
    assert b.get(0) is True
    assert b.get(1) is False
    assert b.get(8) is False  # Out of index


def test_session_stats_properties():
    data = {
        "activeTorrentCount": 1,
        "downloadSpeed": 100,
        "pausedTorrentCount": 0,
        "torrentCount": 1,
        "uploadSpeed": 50,
        "cumulative-stats": {
            "downloadedBytes": 1000,
            "filesAdded": 1,
            "secondsActive": 10,
            "sessionCount": 1,
            "uploadedBytes": 500,
        },
        "current-stats": {
            "downloadedBytes": 100,
            "filesAdded": 0,
            "secondsActive": 5,
            "sessionCount": 1,
            "uploadedBytes": 50,
        },
    }
    s = SessionStats(fields=data)
    assert s.active_torrent_count == 1
    assert s.download_speed == 100
    assert s.paused_torrent_count == 0
    assert s.torrent_count == 1
    assert s.upload_speed == 50

    assert s.cumulative_stats.downloaded_bytes == 1000
    assert s.cumulative_stats.uploaded_bytes == 500
    assert s.cumulative_stats.files_added == 1
    assert s.cumulative_stats.session_count == 1
    assert s.cumulative_stats.seconds_active == 10

    assert s.current_stats.downloaded_bytes == 100


def test_torrent_full_attributes():
    data = {
        "id": 1,
        "name": "name",
        "status": 0,
        "hashString": "hash",
        "activityDate": 100,
        "addedDate": 100,
        "bandwidthPriority": 1,
        "comment": "comment",
        "corruptEver": 0,
        "creator": "creator",
        "desiredAvailable": 100,
        "doneDate": 100,
        "downloadDir": "dir",
        "downloadedEver": 100,
        "downloadLimit": 100,
        "downloadLimited": True,
        "editDate": 100,
        "error": 0,
        "errorString": "",
        "eta": 100,
        "etaIdle": 100,
        "file-count": 1,
        "haveUnchecked": 0,
        "haveValid": 0,
        "honorsSessionLimits": True,
        "isFinished": True,
        "isPrivate": True,
        "isStalled": False,
        "labels": ["label"],
        "leftUntilDone": 0,
        "magnetLink": "magnet",
        "manualAnnounceTime": 100,
        "maxConnectedPeers": 100,
        "metadataPercentComplete": 1.0,
        "peer-limit": 100,
        "peersConnected": 10,
        "peersGettingFromUs": 5,
        "peersSendingToUs": 5,
        "percentDone": 1.0,
        "pieceCount": 100,
        "pieceSize": 1024,
        "queuePosition": 0,
        "rateDownload": 100,
        "rateUpload": 100,
        "recheckProgress": 0.0,
        "secondsDownloading": 100,
        "secondsSeeding": 100,
        "seedIdleLimit": 30,
        "seedIdleMode": 1,
        "seedRatioLimit": 2.0,
        "seedRatioMode": 1,
        "sizeWhenDone": 1000,
        "startDate": 100,
        "torrentFile": "file",
        "totalSize": 1000,
        "uploadLimit": 100,
        "uploadLimited": True,
        "uploadedEver": 100,
        "uploadRatio": 1.0,
        "wanted": [1],
        "webseedsSendingToUs": 0,
        "primary-mime-type": "video/mp4",
        "group": "group",
        "peersFrom": {
            "fromCache": 1,
            "fromDht": 2,
            "fromIncoming": 3,
            "fromLpd": 4,
            "fromLtep": 5,
            "fromPex": 6,
            "fromTracker": 7,
        },
        "files": [{"name": "f1", "bytesCompleted": 100, "length": 1000}],
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "trackers": [{"announce": "url", "id": 1, "scrape": "url", "tier": 1}],
        "trackerStats": [
            {
                "announce": "url",
                "announceState": 1,
                "downloadCount": 1,
                "hasAnnounced": True,
                "hasScraped": True,
                "host": "host",
                "id": 1,
                "isBackup": False,
                "lastAnnouncePeerCount": 1,
                "lastAnnounceResult": "success",
                "lastAnnounceStartTime": 100,
                "lastAnnounceSucceeded": True,
                "lastAnnounceTime": 100,
                "lastAnnounceTimedOut": False,
                "lastScrapeResult": "success",
                "lastScrapeStartTime": 100,
                "lastScrapeSucceeded": True,
                "lastScrapeTime": 100,
                "lastScrapeTimedOut": False,
                "leecherCount": 1,
                "nextAnnounceTime": 100,
                "nextScrapeTime": 100,
                "scrape": "url",
                "scrapeState": 1,
                "seederCount": 1,
                "tier": 1,
            }
        ],
        "peers": [
            {
                "address": "1.2.3.4",
                "clientName": "client",
                "clientIsChoked": False,
                "clientIsInterested": True,
                "flagStr": "E",
                "isDownloadingFrom": True,
                "isEncrypted": True,
                "isIncoming": False,
                "isUploadingTo": False,
                "isUTP": False,
                "peerIsChoked": True,
                "peerIsInterested": False,
                "port": 51413,
                "progress": 0.5,
                "rateToClient": 100,
                "rateToPeer": 100,
            }
        ],
    }
    t = Torrent(fields=data)

    # Dictionary of simple expected values to iterate through
    expected_simple = {
        "id": 1,
        "name": "name",
        "status": "stopped",
        "hashString": "hash",
        "hash_string": "hash",
        "bandwidth_priority": Priority(1),
        "comment": "comment",
        "corrupt_ever": 0,
        "creator": "creator",
        "desired_available": 100,
        "download_dir": "dir",
        "downloaded_ever": 100,
        "download_limit": 100,
        "download_limited": True,
        "error": 0,
        "error_string": "",
        "file_count": 1,
        "have_unchecked": 0,
        "have_valid": 0,
        "honors_session_limits": True,
        "is_finished": True,
        "is_private": True,
        "is_stalled": False,
        "labels": ["label"],
        "left_until_done": 0,
        "magnet_link": "magnet",
        "max_connected_peers": 100,
        "metadata_percent_complete": 1.0,
        "peer_limit": 100,
        "peers_connected": 10,
        "peers_getting_from_us": 5,
        "peers_sending_to_us": 5,
        "percent_done": 1.0,
        "piece_count": 100,
        "piece_size": 1024,
        "queue_position": 0,
        "rate_download": 100,
        "rate_upload": 100,
        "recheck_progress": 0.0,
        "seconds_downloading": 100,
        "seconds_seeding": 100,
        "seed_idle_limit": 30,
        "seed_idle_mode": 1,
        "seed_ratio_limit": 2.0,
        "seed_ratio_mode": 1,
        "size_when_done": 1000,
        "torrent_file": "file",
        "total_size": 1000,
        "upload_limit": 100,
        "upload_limited": True,
        "uploaded_ever": 100,
        "upload_ratio": 1.0,
        "wanted": [1],
        "webseeds_sending_to_us": 0,
        "group": "group",
        "primary_mime_type": "video/mp4",
    }

    for attr, expected in expected_simple.items():
        assert getattr(t, attr) == expected, f"Torrent attribute '{attr}' mismatch"

    # Date/Time properties checks (using timestamp)
    date_properties = [
        "activity_date",
        "added_date",
        "done_date",
        "edit_date",
        "manual_announce_time",
        "start_date",
    ]
    for date_prop in date_properties:
        assert getattr(t, date_prop).timestamp() == 100, f"{date_prop} mismatch"

    # Complex object checks
    assert t.eta.days == 0
    assert t.eta_idle.days == 0

    assert len(t.get_files()) == 1
    assert t.get_files()[0].name == "f1"

    assert len(t.trackers) == 1
    assert t.trackers[0].announce == "url"

    assert len(t.tracker_stats) == 1
    assert t.tracker_stats[0].host == "host"

    assert len(t.peers) == 1
    assert t.peers[0].address == "1.2.3.4"

    assert t.peers_from.from_cache == 1
    assert t.peers_from.from_dht == 2


def test_session_full_attributes():
    data = {
        "alt-speed-down": 100,
        "alt-speed-enabled": True,
        "alt-speed-time-begin": 100,
        "alt-speed-time-day": 1,
        "alt-speed-time-enabled": True,
        "alt-speed-time-end": 200,
        "alt-speed-up": 100,
        "blocklist-enabled": True,
        "blocklist-size": 10,
        "blocklist-url": "url",
        "cache-size-mb": 10,
        "config-dir": "dir",
        "dht-enabled": True,
        "download-dir": "dir",
        "download-dir-free-space": 1000,
        "download-queue-enabled": True,
        "download-queue-size": 5,
        "encryption": "preferred",
        "idle-seeding-limit": 30,
        "idle-seeding-limit-enabled": True,
        "incomplete-dir": "dir",
        "incomplete-dir-enabled": True,
        "lpd-enabled": True,
        "peer-limit-global": 200,
        "peer-limit-per-torrent": 50,
        "peer-port": 51413,
        "peer-port-random-on-start": False,
        "pex-enabled": True,
        "port-forwarding-enabled": True,
        "queue-stalled-enabled": True,
        "queue-stalled-minutes": 10,
        "rename-partial-files": True,
        "rpc-version": 17,
        "rpc-version-semver": "5.3.0",
        "rpc-version-minimum": 15,
        "script-torrent-done-enabled": True,
        "script-torrent-done-filename": "done.sh",
        "seed-queue-enabled": True,
        "seed-queue-size": 5,
        "seedRatioLimit": 2.0,
        "seedRatioLimited": True,
        "speed-limit-down": 1000,
        "speed-limit-down-enabled": True,
        "speed-limit-up": 1000,
        "speed-limit-up-enabled": True,
        "start-added-torrents": True,
        "trash-original-torrent-files": True,
        "utp-enabled": True,
        "version": "4.0.0",
        "script-torrent-added-filename": "added.sh",
        "script-torrent-added-enabled": True,
        "script-torrent-done-seeding-filename": "seeding.sh",
        "script-torrent-done-seeding-enabled": True,
        "default-trackers": ["tracker"],
        "units": {
            "speed-units": ["a"],
            "speed-bytes": 1,
            "size-units": ["b"],
            "size-bytes": 1,
            "memory-units": ["c"],
            "memory-bytes": 1,
        },
    }
    s = Session(fields=data)

    expected_simple = {
        "alt_speed_down": 100,
        "alt_speed_enabled": True,
        "alt_speed_time_begin": 100,
        "alt_speed_time_day": 1,
        "alt_speed_time_enabled": True,
        "alt_speed_time_end": 200,
        "alt_speed_up": 100,
        "blocklist_enabled": True,
        "blocklist_size": 10,
        "blocklist_url": "url",
        "cache_size_mb": 10,
        "config_dir": "dir",
        "dht_enabled": True,
        "download_dir": "dir",
        "download_dir_free_space": 1000,
        "download_queue_enabled": True,
        "download_queue_size": 5,
        "encryption": "preferred",
        "idle_seeding_limit": 30,
        "idle_seeding_limit_enabled": True,
        "incomplete_dir": "dir",
        "incomplete_dir_enabled": True,
        "lpd_enabled": True,
        "peer_limit_global": 200,
        "peer_limit_per_torrent": 50,
        "peer_port": 51413,
        "peer_port_random_on_start": False,
        "pex_enabled": True,
        "port_forwarding_enabled": True,
        "queue_stalled_enabled": True,
        "queue_stalled_minutes": 10,
        "rename_partial_files": True,
        "rpc_version": 17,
        "rpc_version_semver": "5.3.0",
        "rpc_version_minimum": 15,
        "script_torrent_done_enabled": True,
        "script_torrent_done_filename": "done.sh",
        "seed_queue_enabled": True,
        "seed_queue_size": 5,
        "seed_ratio_limit": 2.0,
        "seed_ratio_limited": True,
        "speed_limit_down": 1000,
        "speed_limit_down_enabled": True,
        "speed_limit_up": 1000,
        "speed_limit_up_enabled": True,
        "start_added_torrents": True,
        "trash_original_torrent_files": True,
        "utp_enabled": True,
        "version": "4.0.0",
        "script_torrent_added_filename": "added.sh",
        "script_torrent_added_enabled": True,
        "script_torrent_done_seeding_filename": "seeding.sh",
        "script_torrent_done_seeding_enabled": True,
        "default_trackers": ["tracker"],
    }

    for attr, expected in expected_simple.items():
        assert getattr(s, attr) == expected, f"Session attribute '{attr}' mismatch"

    # Units check
    assert s.units.speed_units == ["a"]
    assert s.units.speed_bytes == 1
    assert s.units.size_units == ["b"]
    assert s.units.size_bytes == 1
    assert s.units.memory_units == ["c"]
    assert s.units.memory_bytes == 1


def test_status_properties():
    assert Status("stopped").stopped is True
    assert Status("check pending").check_pending is True
    assert Status("checking").checking is True
    assert Status("download pending").download_pending is True
    assert Status("downloading").downloading is True
    assert Status("seed pending").seed_pending is True
    assert Status("seeding").seeding is True
    assert str(Status("stopped")) == "stopped"


def test_torrent_files_attributes():
    """
    Verify that get_files() correctly combines 'files' and 'fileStats'
    into rich File objects with all attributes correctly mapped.
    """
    data = {
        "id": 1,
        "files": [{"name": "file1", "bytesCompleted": 100, "length": 1000}],
        "fileStats": [{"bytesCompleted": 100, "wanted": True, "priority": 1}],
        "priorities": [1],
        "wanted": [1],
    }
    t = Torrent(fields=data)
    files = t.get_files()

    assert len(files) == 1
    f = files[0]
    assert f.name == "file1"
    assert f.completed == 100
    assert f.size == 1000
    assert f.selected is True
    assert f.priority == Priority(1)
