import pytest

from transmission_rpc import from_url


def test_from_url_invalid_scheme() -> None:
    with pytest.raises(ValueError, match="unknown url scheme"):
        from_url("ftp://127.0.0.1")


def test_from_url_http_unix_no_host() -> None:
    with pytest.raises(ValueError, match=r"http\+unix URL is missing Unix socket path"):
        from_url("http+unix://")
