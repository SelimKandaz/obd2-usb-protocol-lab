from __future__ import annotations

import pytest

from vod700.mock.replay import DeviceDisconnected, Exchange, ReplayDevice


def test_normal_then_timeout():
    dev = ReplayDevice([Exchange(0x81, b"\x01\x02"), Exchange(0x81, b"", "timeout")])
    assert dev.read(0x81) == b"\x01\x02"
    with pytest.raises(TimeoutError):
        dev.read(0x81)


def test_truncated_bulk():
    dev = ReplayDevice([Exchange(0x82, bytes(64), "truncated")])
    out = dev.read(0x82, max_len=64)
    assert 0 < len(out) < 64


def test_duplicate_response_returned_twice():
    dev = ReplayDevice([Exchange(0x81, b"\xaa\xbb", "duplicate")])
    assert dev.read(0x81) == b"\xaa\xbb"
    assert dev.read(0x81) == b"\xaa\xbb"


def test_disconnect_raises():
    dev = ReplayDevice([Exchange(0x81, b"", "disconnect")])
    with pytest.raises(DeviceDisconnected):
        dev.read(0x81)


def test_write_is_recorded_not_forwarded():
    dev = ReplayDevice()
    assert dev.write(0x01, b"\x01\x02\x03") == 3
    assert dev.sent == [(0x01, b"\x01\x02\x03")]


def test_exhausted_script_times_out():
    dev = ReplayDevice()
    with pytest.raises(TimeoutError):
        dev.read(0x81)
