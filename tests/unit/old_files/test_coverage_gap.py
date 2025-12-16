import io

from transmission_rpc.client import _try_read_torrent
from transmission_rpc.torrent import Status


def test_status_properties():
    assert Status("stopped").stopped is True
    assert Status("check pending").check_pending is True
    assert Status("checking").checking is True
    assert Status("download pending").download_pending is True
    assert Status("downloading").downloading is True
    assert Status("seed pending").seed_pending is True
    assert Status("seeding").seeding is True
    assert str(Status("stopped")) == "stopped"


def test_try_read_torrent_path(tmp_path):
    p = tmp_path / "test.torrent"
    p.write_bytes(b"data")
    assert _try_read_torrent(p) == "ZGF0YQ=="


def test_try_read_torrent_file_obj():
    f = io.BytesIO(b"data")
    assert _try_read_torrent(f) == "ZGF0YQ=="


def test_try_read_torrent_bytes():
    assert _try_read_torrent(b"data") == "ZGF0YQ=="


def test_try_read_torrent_url():
    assert _try_read_torrent("http://example.com/t.torrent") is None
    assert _try_read_torrent("magnet:?xt=urn:btih:hash") is None
