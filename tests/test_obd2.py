from __future__ import annotations

import pytest

from vod700.obd2 import (
    CanFrame,
    IsoTpError,
    IsoTpReassembler,
    decode_dtc_response,
    decode_mode01_response,
    decode_vin_response,
    encode_isotp,
    parse_can_line,
)


def test_can_frame_round_trip_socketcan_line():
    frame = parse_can_line("7E8#04410C1AF8000000")
    assert frame.arbitration_id == 0x7E8
    assert frame.extended is False
    assert frame.dlc == 8
    assert frame.to_socketcan() == "7E8#04410C1AF8000000"


def test_isotp_single_frame_and_rpm_pid():
    frame = parse_can_line("7E8#04410C1AF8000000")
    payload = IsoTpReassembler().feed(frame)
    assert payload == bytes.fromhex("410C1AF8")
    decoded = decode_mode01_response(payload or b"")
    assert decoded.name == "engine_rpm"
    assert decoded.value == 1726.0
    assert decoded.unit == "rpm"


def test_isotp_multi_frame_reassembly_and_vin():
    payload = b"I\x02" + b"WVWZZZ1JZXW000001"
    frames = encode_isotp(payload, 0x7E8)
    reassembler = IsoTpReassembler()
    result = None
    for frame in frames:
        result = reassembler.feed(frame)
    assert result == payload
    assert decode_vin_response(result or b"") == "WVWZZZ1JZXW000001"


def test_dtc_decode_omits_zero_terminator():
    assert [d.code for d in decode_dtc_response(bytes.fromhex("4301000000"))] == ["P0100"]


def test_isotp_rejects_sequence_gap():
    reassembler = IsoTpReassembler()
    frames = encode_isotp(b"123456789", 0x7E8)
    reassembler.feed(frames[0])
    bad = CanFrame(0x7E8, bytes.fromhex("2233343536373800"))
    with pytest.raises(IsoTpError, match="sequence"):
        reassembler.feed(bad)


def test_can_and_obd2_validation_errors():
    with pytest.raises(ValueError):
        parse_can_line("7E8#0")
    with pytest.raises(ValueError):
        decode_mode01_response(bytes.fromhex("410C"))
