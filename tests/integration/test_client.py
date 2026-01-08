import base64
import contextlib
import pathlib
import time
from typing import Literal
from unittest import mock
from urllib.parse import urljoin

import pytest

from tests.util import ServerTooLowError, skip_on
from transmission_rpc.client import Client, _try_read_torrent
from transmission_rpc.error import TransmissionAuthError, TransmissionError
from transmission_rpc.types import File


@pytest.mark.parametrize(
    ("protocol", "username", "password", "host", "port", "path"),
    [
        (
            "https",
            "a+2da/s a?s=d$",
            "a@as +@45/:&*^",
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
        (
            "http",
            "/",
            None,
            "127.0.0.1",
            2333,
            "/transmission/",
        ),
    ],
)
def test_client_parse_url(protocol: Literal["http", "https"], username, password, host, port, path):
    """
    Verify that the Client correctly parses the URL from the given parameters.
    """
    with (
        mock.patch("transmission_rpc.client.Client._request"),
        mock.patch("transmission_rpc.client.Client.get_session"),
    ):
        client = Client(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
            path=path,
        )

        assert client._url == f"{protocol}://{host}:{port}{urljoin(path, 'rpc')}"  # noqa: SLF001


def hash_to_magnet(h):
    """Helper function to convert a torrent hash to a magnet link."""
    return f"magnet:?xt=urn:btih:{h}"


torrent_hash = "e84213a794f3ccd890382a54a64ca68b7e925433"
magnet_url = f"magnet:?xt=urn:btih:{torrent_hash}"
torrent_hash2 = "9fc20b9e98ea98b4a35e6223041a5ef94ea27809"
torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"


def test_client_add_kwargs():
    """
    Verify that `add_torrent` correctly translates keyword arguments into the RPC request payload.
    """
    m = mock.Mock(return_value={"hello": "workd"})
    with mock.patch("transmission_rpc.client.Client._request", m):
        with mock.patch("transmission_rpc.client.Client.get_session"):
            c = Client()
            c.add_torrent(
                torrent_url,
                download_dir="dd",
                files_unwanted=[1, 2],
                files_wanted=[3, 4],
                paused=False,
                peer_limit=5,
                priority_high=[6],
                priority_low=[7],
                priority_normal=[8],
                cookies="coo",
                bandwidthPriority=4,
            )
        m.assert_called_with(
            "torrent-add",
            {
                "filename": torrent_url,
                "download-dir": "dd",
                "files-unwanted": [1, 2],
                "files-wanted": [3, 4],
                "paused": False,
                "peer-limit": 5,
                "priority-high": [6],
                "priority-low": [7],
                "priority-normal": [8],
                "cookies": "coo",
                "bandwidthPriority": 4,
            },
            timeout=None,
        )


def test_client_add_url():
    """
    Verify that `_try_read_torrent` returns None for a standard HTTP URL,
    indicating it should be handled by the daemon directly.
    """
    assert _try_read_torrent(torrent_url) is None, "Should return None for HTTP URLs (let daemon handle it)"


def test_client_add_magnet():
    """
    Verify that `_try_read_torrent` returns None for a magnet link,
    indicating it should be handled by the daemon directly.
    """
    assert _try_read_torrent(magnet_url) is None, "Should return None for magnet URLs (let daemon handle it)"


def test_client_add_pathlib_path():
    """
    Verify that `_try_read_torrent` correctly reads and base64 encodes the content of a local file provided as a Path object.
    """
    p = pathlib.Path("tests/fixtures/iso.torrent")
    b64 = base64.b64encode(p.read_bytes()).decode()
    assert _try_read_torrent(p) == b64, "Should correctly read and base64 encode content from a Path object"


def test_client_add_read_file_in_base64():
    """
    Verify that `_try_read_torrent` correctly reads and base64 encodes the content of an open file object.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
        f.seek(0)
        data = _try_read_torrent(f)

    assert base64.b64encode(content).decode() == data, "Should correctly base64 encode content from a file object"


def test_client_add_torrent_bytes():
    """
    Verify that `_try_read_torrent` correctly base64 encodes raw bytes content.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        content = f.read()
    data = _try_read_torrent(content)
    assert base64.b64encode(content).decode() == data, "Should correctly base64 encode raw bytes"


def test_real_add_magnet(tr_client: Client):
    """
    Integration test: Verify adding a torrent via magnet link actually adds it to the daemon.
    """
    tr_client.add_torrent(magnet_url)
    assert len(tr_client.get_torrents()) == 1, "Transmission daemon should have exactly 1 task after adding magnet link"


def test_real_add_torrent_fd(tr_client: Client):
    """
    Integration test: Verify adding a torrent via an open file descriptor.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, (
        "Transmission daemon should have exactly 1 task after adding torrent file"
    )


def test_real_add_torrent_http(tr_client: Client):
    """
    Integration test: Verify adding a torrent via an HTTP URL.
    """
    tr_client.add_torrent(torrent_url)
    assert len(tr_client.get_torrents()) == 1, "Transmission daemon should have exactly 1 task after adding HTTP URL"


def test_real_stop(tr_client: Client, fake_hash_factory):
    """
    Integration test: Verify stopping a torrent works.
    """
    info_hash = fake_hash_factory()
    url = hash_to_magnet(info_hash)
    tr_client.add_torrent(url)
    tr_client.stop_torrent(info_hash)
    assert len(tr_client.get_torrents()) == 1, "Transmission should still have the task listed"
    ret = False

    for _ in range(50):
        time.sleep(0.2)
        if tr_client.get_torrents()[0].status == "stopped":
            ret = True
            break

    assert ret, "Torrent status should eventually become 'stopped'"


def test_real_torrent_start_all(tr_client: Client, fake_hash_factory):
    """
    Integration test: Verify `start_all` starts all paused torrents.
    """
    tr_client.add_torrent(torrent_url, paused=True, timeout=10)
    for torrent in tr_client.get_torrents():
        assert torrent.stopped or torrent.checking, "Newly added torrent should be stopped or checking initially"

    tr_client.start_all()
    for torrent in tr_client.get_torrents():
        assert torrent.downloading or torrent.checking, "All torrents should be downloading or checking after start_all"


def test_real_session_get(tr_client: Client):
    """
    Integration test: Verify `get_session` returns session information without error.
    """
    tr_client.get_session()


def test_real_free_space(tr_client: Client):
    """
    Integration test: Verify `free_space` returns valid information for the download directory.
    """
    session = tr_client.get_session()
    with contextlib.suppress(TransmissionError):
        tr_client.free_space(session.download_dir)


def test_real_session_stats(tr_client: Client):
    """
    Integration test: Verify `session_stats` returns statistics without error.
    """
    tr_client.session_stats()


def test_wrong_logger():
    """
    Verify that initializing Client with an invalid logger raises a TypeError.
    """
    with pytest.raises(TypeError):
        Client(logger="something")


def test_real_torrent_attr_type(tr_client: Client):
    """
    Integration test: Verify that torrent attributes have the expected types.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    for torrent in tr_client.get_torrents():
        assert isinstance(torrent.id, int), "Torrent ID should be an integer"
        assert isinstance(torrent.name, str), "Torrent name should be a string"


def test_real_torrent_get_files(tr_client: Client):
    """
    Integration test: Verify that `get_files` returns a list of File objects.
    """
    with open("tests/fixtures/iso.torrent", "rb") as f:
        tr_client.add_torrent(f)
    assert len(tr_client.get_torrents()) == 1, "Transmission should have exactly 1 task"
    for torrent in tr_client.get_torrents():
        files = torrent.get_files()
        assert len(files) > 0, "Torrent should have files"
        for file in files:
            assert isinstance(file, File), "Each item in get_files should be a File object"


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_raise_unauthorized(status_code):
    """
    Verify that Client raises TransmissionAuthError when the server returns 401 or 403.
    """
    m = mock.Mock(return_value=mock.Mock(status=status_code))
    with mock.patch("urllib3.HTTPConnectionPool.request", m), pytest.raises(TransmissionAuthError):
        Client()


@skip_on(ServerTooLowError, "group methods is added in rpc version 17")
def test_groups(tr_client: Client):
    """
    Integration test: Verify group operations (set_group, get_groups).
    Skips if RPC version is too low.
    """
    if tr_client.get_session().rpc_version < 17:
        raise ServerTooLowError  # pragma: no cover

    tr_client.set_group("test.1")
    groups = tr_client.get_groups()

    assert "test.1" in groups, "The set group 'test.1' should be present in the groups list"
