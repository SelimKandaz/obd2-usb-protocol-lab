from __future__ import annotations

from vod700.protocol.models import (
    Direction,
    Field,
    ParsedFrame,
    TransferType,
    UsbTransfer,
)


def test_usb_transfer_dict_roundtrip_fields():
    t = UsbTransfer(
        index=3,
        timestamp=1.5,
        endpoint=0x82,
        direction=Direction.IN,
        transfer_type=TransferType.BULK,
        payload=b"\xde\xad\xbe\xef",
        bus=1,
        address=9,
    )
    d = t.to_dict()
    assert d["endpoint_hex"] == "0x82"
    assert d["direction"] == "IN"
    assert d["payload_hex"] == "deadbeef"
    assert d["length"] == 4
    assert t.endpoint_number == 0x02


def test_parsed_frame_coverage_and_unexplained():
    raw = b"\xaa\xbb\xcc\xdd"
    frame = ParsedFrame(
        raw=raw,
        fields=[
            Field("magic", 0, 1, raw[:1], raw[0]),
            Field("unknown", 1, 3, raw[1:], raw[1:]),
        ],
    )
    assert frame.covered_offsets() == {0}
    assert frame.unexplained_bytes() == b"\xbb\xcc\xdd"
    assert 0.0 < frame.coverage() < 1.0
