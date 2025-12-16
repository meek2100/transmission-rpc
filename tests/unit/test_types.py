from transmission_rpc.client import _parse_torrent_id, _parse_torrent_ids
from transmission_rpc.constants import Priority
from transmission_rpc.session import Session
from transmission_rpc.torrent import Status, Torrent


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

    # Detailed verification of nested structures (previously in separate files)
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
