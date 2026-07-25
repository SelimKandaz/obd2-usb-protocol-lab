from __future__ import annotations

import pytest

from vod700.capture.usbpcap import decode_usbpcap
from vod700.mock.fixtures import make_usbpcap_record
from vod700.protocol.models import Direction, TransferType


def test_decode_interrupt_in():
    rec = make_usbpcap_record(
        endpoint=0x81, payload=b"\x55\x01", transfer_type=TransferType.INTERRUPT, bus=1, address=9
    )
    d = decode_usbpcap(rec)
    assert d.endpoint == 0x81
    assert d.direction is Direction.IN
    assert d.transfer_type is TransferType.INTERRUPT
    assert d.bus == 1 and d.device == 9
    assert d.payload == b"\x55\x01"


def test_decode_bulk_out():
    rec = make_usbpcap_record(endpoint=0x02, payload=bytes(64), transfer_type=TransferType.BULK)
    d = decode_usbpcap(rec)
    assert d.direction is Direction.OUT
    assert d.transfer_type is TransferType.BULK
    assert len(d.payload) == 64


def test_decode_classifies_live_urb_and_phase():
    rec = make_usbpcap_record(
        endpoint=0x80,
        payload=b"\x12",
        transfer_type=TransferType.CONTROL,
        irp_id=0x1234,
    )
    d = decode_usbpcap(rec)
    assert d.is_synthetic is False
    assert d.phase == "completion"


def test_decode_classifies_injected_descriptor():
    rec = make_usbpcap_record(endpoint=0x80, payload=b"\x12", transfer_type=TransferType.CONTROL)
    d = decode_usbpcap(rec)
    assert d.is_synthetic is True
    assert d.phase == "completion"


def test_decode_rejects_too_short():
    with pytest.raises(ValueError):
        decode_usbpcap(b"\x00\x00")
