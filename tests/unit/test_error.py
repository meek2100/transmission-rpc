from unittest import mock

import pytest

from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)


def test_transmission_error_str_basic() -> None:
    e = TransmissionError("message")
    assert str(e) == "message"


def test_transmission_error_str_with_original() -> None:
    original = mock.MagicMock()
    original.__str__.return_value = "original error"  # type: ignore[attr-defined]
    e = TransmissionError("message", original=original)
    # type(mock.Mock()).__name__ is MagicMock
    assert "Original exception: MagicMock" in str(e)
    assert '"original error"' in str(e)


def test_transmission_error_deprecated_property() -> None:
    e = TransmissionError("message", raw_response="raw")
    with pytest.warns(DeprecationWarning, match="use .raw_response instead"):
        assert e.rawResponse == "raw"


def test_auth_error() -> None:
    e = TransmissionAuthError("auth")
    assert isinstance(e, TransmissionError)


def test_connect_error() -> None:
    e = TransmissionConnectError("connect")
    assert isinstance(e, TransmissionError)


def test_timeout_error() -> None:
    e = TransmissionTimeoutError("timeout")
    assert isinstance(e, TransmissionConnectError)
