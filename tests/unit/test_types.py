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
        "file-count": 1,
        "isFinished": True,
        "labels": ["label"],
        "leftUntilDone": 0,
        "magnetLink": "magnet",
        "percentDone": 1.0,
        "queuePosition": 0,
        "rateDownload": 100,
        "rateUpload": 100,
        "sizeWhenDone": 1000,
        "startDate": 100,
        "totalSize": 1000,
        "uploadedEver": 100,
        "uploadRatio": 1.0,
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
    # Verification of all core calculated properties
    assert t.id == 1
    assert t.status == "stopped"
    assert t.priority == Priority.High
    assert t.progress == 100.0
    assert t.ratio == 1.0

    # Detailed verification of nested structures
    files = t.get_files()
    assert len(files) == 1
    assert files[0].name == "f1"
    assert files[0].completed == 100
    assert files[0].size == 1000
    assert files[0].selected is True
    assert files[0].priority == Priority(1)

    assert len(t.trackers) == 1
    assert t.trackers[0].announce == "url"
    assert t.trackers[0].tier == 1

    assert len(t.peers) == 1
    assert t.peers[0].address == "1.2.3.4"
    assert t.peers[0].client_name == "client"
    assert t.peers[0].rate_to_client == 100

    assert t.peers_from.from_cache == 1
    assert t.peers_from.from_dht == 2


def test_session_full_attributes():
    data = {
        "alt-speed-down": 100,
        "alt-speed-enabled": True,
        "blocklist-enabled": True,
        "download-dir": "dir",
        "encryption": "preferred",
        "peer-port": 51413,
        "rpc-version": 17,
        "version": "4.0.0",
        "units": {"speed-units": ["kB/s"], "speed-bytes": 1024},
    }
    s = Session(fields=data)
    assert s.alt_speed_down == 100
    assert s.rpc_version == 17
    assert s.units.speed_units == ["kB/s"]


def test_status_properties():
    assert Status("stopped").stopped is True
    assert Status("check pending").check_pending is True
    assert Status("checking").checking is True
    assert Status("download pending").download_pending is True
    assert Status("downloading").downloading is True
    assert Status("seed pending").seed_pending is True
    assert Status("seeding").seeding is True
    assert str(Status("stopped")) == "stopped"
