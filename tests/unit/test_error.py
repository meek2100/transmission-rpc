from unittest import mock

import pytest

from transmission_rpc.error import TransmissionError


def test_error_str_with_original() -> None:
    original = mock.Mock()
    original.__str__ = mock.Mock(return_value="original error")  # type: ignore[method-assign]
    type(original).__name__ = "OriginalError"
    err = TransmissionError("message", original=original)
    assert str(err) == 'message Original exception: OriginalError, "original error"'


def test_deprecated_raw_response() -> None:
    err = TransmissionError("message", raw_response="raw")
    with pytest.warns(DeprecationWarning, match="use .raw_response instead"):
        assert err.rawResponse == "raw"
