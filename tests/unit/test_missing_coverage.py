from transmission_rpc.session import Session
from transmission_rpc.types import Container


def test_container_repr() -> None:
    """Test Container.__repr__ which is missing coverage."""
    c = Container(fields={"key": "value"})
    assert repr(c) == "<Container fields={'key': 'value'}>"


def test_session_default_trackers_branches() -> None:
    """
    Test branches in default_trackers property.
    Existing tests only cover the None case.
    """
    # Case 1: default-trackers is a newline-separated string
    s1 = Session(fields={"default-trackers": "http://t1.com\nhttp://t2.com"})
    assert s1.default_trackers == ["http://t1.com", "http://t2.com"]

    # Case 2: default-trackers is already a list
    s2 = Session(fields={"default-trackers": ["http://t3.com"]})
    assert s2.default_trackers == ["http://t3.com"]


def test_script_torrent_added_filename() -> None:
    """
    Explicitly test script_torrent_added_filename to ensure coverage
    at the reported line 372.
    """
    s = Session(fields={"script-torrent-added-filename": "my_script.sh"})
    assert s.script_torrent_added_filename == "my_script.sh"
