"""Builders for SYNTHETIC test fixtures.

Everything here is fabricated for testing. None of it is captured from the real
device, so nothing proprietary is embedded. The synthetic USBPcap writer lets us
round-trip the native reader/decoder without tshark or hardware.
"""
from __future__ import annotations

import struct

from ..protocol.models import Direction, TransferType, UsbTransfer

# USBPcap transfer codes
_TC = {TransferType.ISOCHRONOUS: 0, TransferType.INTERRUPT: 1, TransferType.CONTROL: 2, TransferType.BULK: 3}


def make_usbpcap_record(
    *,
    endpoint: int,
    payload: bytes,
    transfer_type: TransferType = TransferType.INTERRUPT,
    bus: int = 1,
    address: int = 9,
    irp_id: int = 0,
) -> bytes:
    """Build one USBPcap pseudo-header + payload (matches usbpcap.decode)."""
    is_in = bool(endpoint & 0x80)
    header_len = 27
    header = struct.pack(
        "<HQIHBHHBBI",
        header_len,               # headerLen
        irp_id,                   # irpId
        0,                        # status
        0x0009,                   # function (URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER)
        0x01 if is_in else 0x00,  # info (PDO->FDO for IN)
        bus,                      # bus
        address,                  # device
        endpoint,                 # endpoint
        _TC[transfer_type],       # transfer
        len(payload),             # dataLength
    )
    assert len(header) == header_len, f"header is {len(header)} bytes, expected {header_len}"
    return header + payload


def _block(block_type: int, body: bytes) -> bytes:
    pad = (-len(body)) % 4
    body = body + b"\x00" * pad
    total = 12 + len(body)
    return struct.pack("<II", block_type, total) + body + struct.pack("<I", total)


def build_usbpcap_pcapng(records: list[tuple[int, bytes]]) -> bytes:
    """Build a little-endian pcapng (linktype 249) from ``(ts_ns, usbpcap_bytes)``.

    ``records`` is a list of ``(timestamp_ns, usbpcap_record_bytes)`` tuples, where
    the record bytes come from :func:`make_usbpcap_record`.
    """
    # SHB
    shb_body = struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1)
    out = bytearray(_block(0x0A0D0D0A, shb_body))
    # IDB: linktype 249, snaplen 0, if_tsresol = 9 (nanoseconds)
    idb_body = struct.pack("<HHI", 249, 0, 0)
    idb_body += struct.pack("<HH", 9, 1) + bytes([9]) + b"\x00" * 3  # if_tsresol option
    idb_body += struct.pack("<HH", 0, 0)  # opt_endofopt
    out += _block(0x00000001, idb_body)
    # EPBs
    for ts_ns, data in records:
        ts_hi = (ts_ns >> 32) & 0xFFFFFFFF
        ts_lo = ts_ns & 0xFFFFFFFF
        epb_body = struct.pack("<IIIII", 0, ts_hi, ts_lo, len(data), len(data)) + data
        out += _block(0x00000006, epb_body)
    return bytes(out)


def synthetic_interrupt_transfers() -> list[UsbTransfer]:
    """A small fabricated interrupt exchange for parser/framing tests.

    The bytes are invented. The final byte of each frame is a trivial XOR8 over
    the preceding bytes so checksum-detector tests have a known-good answer.
    """
    def framed(body: bytes) -> bytes:
        acc = 0
        for b in body:
            acc ^= b
        return body + bytes([acc])

    out: list[UsbTransfer] = []
    bodies = [b"\xaa\x01\x00", b"\xaa\x01\x01", b"\xaa\x02\x02"]
    ts = 0.0
    for i, body in enumerate(bodies):
        frame = framed(body).ljust(16, b"\x00")
        out.append(
            UsbTransfer(
                index=i * 2,
                timestamp=ts,
                endpoint=0x01,
                direction=Direction.OUT,
                transfer_type=TransferType.INTERRUPT,
                payload=frame,
                bus=1,
                address=9,
                capture_id="synthetic",
            )
        )
        ts += 0.01
        out.append(
            UsbTransfer(
                index=i * 2 + 1,
                timestamp=ts,
                endpoint=0x81,
                direction=Direction.IN,
                transfer_type=TransferType.INTERRUPT,
                payload=framed(b"\x55\x01").ljust(16, b"\x00"),
                bus=1,
                address=9,
                capture_id="synthetic",
            )
        )
        ts += 0.02
    return out
