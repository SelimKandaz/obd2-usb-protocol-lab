from __future__ import annotations

from vod700.capture.transactions import (
    USBD_STATUS_CANCELED,
    correlate_feedback_reads,
    correlate_urb_transactions,
)
from vod700.protocol.models import Direction, TransferType, UsbTransfer


def _transfer(
    index: int,
    *,
    endpoint: int,
    direction: Direction,
    payload: bytes,
    irp_id: int,
    completion: bool,
    status: int = 0,
) -> UsbTransfer:
    return UsbTransfer(
        index=index,
        timestamp=index / 1000,
        endpoint=endpoint,
        direction=direction,
        transfer_type=TransferType.BULK if endpoint == 0x82 else TransferType.INTERRUPT,
        payload=payload,
        bus=1,
        address=6,
        status=status,
        irp_id=irp_id,
        usbpcap_info=1 if completion else 0,
    )


def test_correlates_reused_irp_as_distinct_submit_completion_pairs():
    transfers = [
        _transfer(0, endpoint=0x82, direction=Direction.IN, payload=b"", irp_id=9, completion=False),
        _transfer(1, endpoint=0x82, direction=Direction.IN, payload=b"first", irp_id=9, completion=True),
        _transfer(2, endpoint=0x82, direction=Direction.IN, payload=b"", irp_id=9, completion=False),
        _transfer(3, endpoint=0x82, direction=Direction.IN, payload=b"second", irp_id=9, completion=True),
    ]
    transactions, orphans = correlate_urb_transactions(transfers)
    assert not orphans
    assert [transaction.payload for transaction in transactions] == [b"first", b"second"]
    assert all(transaction.succeeded for transaction in transactions)


def test_refuses_cross_endpoint_completion_for_the_same_irp_until_a_matching_completion_arrives():
    transfers = [
        _transfer(0, endpoint=0x82, direction=Direction.IN, payload=b"", irp_id=9, completion=False),
        _transfer(1, endpoint=0x81, direction=Direction.IN, payload=b"wrong", irp_id=9, completion=True),
        _transfer(2, endpoint=0x82, direction=Direction.IN, payload=b"right", irp_id=9, completion=True),
    ]
    transactions, orphans = correlate_urb_transactions(transfers)
    assert len(orphans) == 1
    assert orphans[0].payload == b"wrong"
    assert len(transactions) == 1
    assert transactions[0].payload == b"right"


def test_feedback_correlation_keeps_cancelled_request_out_of_device_responses():
    request = bytes.fromhex("55aa060000fb01001000000000000011")
    acknowledgement = bytes.fromhex("aa558600000000000000000000000085")
    bulk_first = bytes.fromhex("aa55aa55") + b"\xff" * 4092
    bulk_second = bytes.fromhex("ffffffff000ff1fe")
    cancelled_request = bytes.fromhex("55aa060010fb01001000000000000021")
    transfers = [
        _transfer(0, endpoint=0x01, direction=Direction.OUT, payload=request, irp_id=1, completion=False),
        _transfer(1, endpoint=0x01, direction=Direction.OUT, payload=b"", irp_id=1, completion=True),
        _transfer(2, endpoint=0x81, direction=Direction.IN, payload=b"", irp_id=2, completion=False),
        _transfer(3, endpoint=0x81, direction=Direction.IN, payload=acknowledgement, irp_id=2, completion=True),
        _transfer(4, endpoint=0x82, direction=Direction.IN, payload=b"", irp_id=3, completion=False),
        _transfer(5, endpoint=0x82, direction=Direction.IN, payload=bulk_first, irp_id=3, completion=True),
        _transfer(6, endpoint=0x82, direction=Direction.IN, payload=b"", irp_id=3, completion=False),
        _transfer(7, endpoint=0x82, direction=Direction.IN, payload=bulk_second, irp_id=3, completion=True),
        _transfer(8, endpoint=0x01, direction=Direction.OUT, payload=cancelled_request, irp_id=4, completion=False),
        _transfer(
            9,
            endpoint=0x01,
            direction=Direction.OUT,
            payload=b"",
            irp_id=4,
            completion=True,
            status=USBD_STATUS_CANCELED,
        ),
    ]

    reads = correlate_feedback_reads(transfers)
    assert len(reads) == 2
    assert reads[0].address == 0x01FB0000
    assert reads[0].observation is not None
    assert reads[0].observation.checksum_valid is True
    assert reads[1].address == 0x01FB1000
    assert reads[1].acknowledgement is None
    assert "CANCELED" in reads[1].note
