import contextlib

from transmission_rpc.session import Session, SessionStats, Stats, Units
from transmission_rpc.torrent import FileStat, Peer, PeersFrom, Status, Torrent, Tracker, TrackerStats, get_status
from transmission_rpc.types import BitMap, Group, PortTestResult


from typing import Any

def check_properties(cls: type, obj: Any) -> None:
    for prop in dir(cls):
        if isinstance(getattr(cls, prop), property):
            with contextlib.suppress(KeyError, DeprecationWarning):
                getattr(obj, prop)

def test_session_properties_access() -> None:
    s = Session(fields={})
    check_properties(Session, s)

def test_session_stats_properties_access() -> None:
    s = SessionStats(fields={})
    check_properties(SessionStats, s)

def test_stats_properties_access() -> None:
    s = Stats(fields={})
    check_properties(Stats, s)

def test_units_properties_access() -> None:
    u = Units(fields={})
    check_properties(Units, u)

def test_torrent_properties_access() -> None:
    t = Torrent(fields={"id": 1})
    check_properties(Torrent, t)

def test_peer_properties_access() -> None:
    p = Peer(fields={})
    check_properties(Peer, p)

def test_peers_from_properties_access() -> None:
    p = PeersFrom(fields={})
    check_properties(PeersFrom, p)

def test_file_stat_properties_access() -> None:
    f = FileStat(fields={})
    check_properties(FileStat, f)

def test_tracker_properties_access() -> None:
    t = Tracker(fields={})
    check_properties(Tracker, t)

def test_tracker_stats_properties_access() -> None:
    t = TrackerStats(fields={})
    check_properties(TrackerStats, t)

def test_status_properties() -> None:
    s = Status("stopped")
    assert s.stopped is True
    assert s.check_pending is False
    assert str(s) == "stopped"

    check_properties(Status, s)

def test_group_properties() -> None:
    fields = {
        "name": "g1",
        "honorsSessionLimits": True,
        "speed-limit-down-enabled": False,
        "speed-limit-down": 100,
        "speed-limit-up-enabled": False,
        "speed-limit-up": 100,
    }
    g = Group(fields=fields)
    assert g.name == "g1"
    assert g.honors_session_limits is True
    assert g.speed_limit_down_enabled is False
    assert g.speed_limit_down == 100
    assert g.speed_limit_up_enabled is False
    assert g.speed_limit_up == 100

def test_port_test_result_properties() -> None:
    fields = {"port-is-open": True, "ip_protocol": "ipv4"}
    r = PortTestResult(fields=fields)
    assert r.port_is_open is True
    assert r.ip_protocol == "ipv4"

def test_bitmap() -> None:
    # 1 byte: 10101010 -> 0xAA.
    # Index 0 is MSB.
    # 0xAA = 170.
    # 10101010
    # 0: True, 1: False, 2: True, 3: False...
    b = BitMap(b"\xAA")
    assert b.get(0) is True
    assert b.get(1) is False
    assert b.get(7) is False
    assert b.get(8) is False  # out of bounds

def test_torrent_rich_fields() -> None:
    fields = {
        "id": 1,
        "eta": -1,
        "etaIdle": -1,
        "pieces": "AA==", # base64 for 0x00
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

def test_session_missing_properties() -> None:
    s = Session(fields={"script-torrent-done-seeding-enabled": True})
    assert s.script_torrent_done_seeding_enabled is True
