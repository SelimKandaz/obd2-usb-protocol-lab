"""Minimal, dependency-free reader for pcapng and classic pcap files.

Supports exactly what is needed for USB capture ingestion:
  * pcapng: Section Header (SHB), Interface Description (IDB), Enhanced Packet
    (EPB) and Simple Packet (SPB) blocks, with per-interface timestamp
    resolution (``if_tsresol``).
  * classic pcap: little/big endian, microsecond and nanosecond magics.

Each yielded :class:`RawPacket` carries the interface link type so the caller can
decide how to decode the payload (see :mod:`vod700.capture.usbpcap`).
"""
from __future__ import annotations

import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# pcapng block types
_SHB = 0x0A0D0D0A
_IDB = 0x00000001
_SPB = 0x00000003
_EPB = 0x00000006

# classic pcap magics -> (endian, time-unit-divisor)
_CLASSIC_MAGICS = {
    b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
    b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
    b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
    b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000),
}


@dataclass
class RawPacket:
    index: int
    timestamp: float
    linktype: int
    data: bytes
    interface_id: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "linktype": self.linktype,
            "interface_id": self.interface_id,
            "length": len(self.data),
        }


def read_packets(path: str | Path) -> list[RawPacket]:
    return list(iter_packets(Path(path).read_bytes()))


def iter_packets(blob: bytes) -> Iterator[RawPacket]:
    if blob[:4] == b"\x0a\x0d\x0d\x0a":
        yield from _iter_pcapng(blob)
    elif blob[:4] in _CLASSIC_MAGICS:
        yield from _iter_classic(blob)
    else:
        raise ValueError(
            f"Unrecognized capture format (first 4 bytes: {blob[:4].hex()}). "
            "Expected pcapng (0a0d0d0a) or classic pcap magic."
        )


# --------------------------------------------------------------------------
# classic pcap
# --------------------------------------------------------------------------
def _iter_classic(blob: bytes) -> Iterator[RawPacket]:
    endian, divisor = _CLASSIC_MAGICS[blob[:4]]
    if len(blob) < 24:
        raise ValueError("truncated classic pcap global header")
    (_magic, _vmaj, _vmin, _tz, _sig, _snap, network) = struct.unpack(endian + "IHHiIII", blob[:24])
    offset = 24
    index = 0
    while offset + 16 <= len(blob):
        ts_sec, ts_frac, incl_len, _orig = struct.unpack(endian + "IIII", blob[offset : offset + 16])
        offset += 16
        data = blob[offset : offset + incl_len]
        if len(data) < incl_len:
            break  # truncated final record
        offset += incl_len
        yield RawPacket(index, ts_sec + ts_frac / divisor, network, data)
        index += 1


# --------------------------------------------------------------------------
# pcapng
# --------------------------------------------------------------------------
def _iter_pcapng(blob: bytes) -> Iterator[RawPacket]:
    # Determine endianness from the SHB byte-order magic at offset 8.
    bom = blob[8:12]
    if bom == b"\x1a\x2b\x3c\x4d":
        endian = ">"
    elif bom == b"\x4d\x3c\x2b\x1a":
        endian = "<"
    else:
        raise ValueError(f"bad pcapng byte-order magic: {bom.hex()}")

    offset = 0
    index = 0
    tsresol_by_iface: dict[int, float] = {}
    iface_linktype: dict[int, int] = {}
    iface_count = 0
    total = len(blob)

    while offset + 12 <= total:
        block_type = struct.unpack(endian + "I", blob[offset : offset + 4])[0]
        block_len = struct.unpack(endian + "I", blob[offset + 4 : offset + 8])[0]
        if block_len < 12 or offset + block_len > total:
            break
        body = blob[offset + 8 : offset + block_len - 4]

        if block_type == _IDB:
            linktype = struct.unpack(endian + "H", body[0:2])[0]
            iface_linktype[iface_count] = linktype
            tsresol_by_iface[iface_count] = _parse_if_tsresol(body[8:], endian)
            iface_count += 1
        elif block_type == _EPB:
            iface_id, ts_hi, ts_lo, cap_len, _orig = struct.unpack(endian + "IIIII", body[0:20])
            data = body[20 : 20 + cap_len]
            unit = tsresol_by_iface.get(iface_id, 1e-6)
            ts = ((ts_hi << 32) | ts_lo) * unit
            yield RawPacket(index, ts, iface_linktype.get(iface_id, -1), data, iface_id)
            index += 1
        elif block_type == _SPB:
            orig_len = struct.unpack(endian + "I", body[0:4])[0]
            cap_len = min(orig_len, len(body) - 4)
            data = body[4 : 4 + cap_len]
            yield RawPacket(index, 0.0, iface_linktype.get(0, -1), data, 0)
            index += 1
        # SHB and any other block types are skipped.

        offset += block_len


def _parse_if_tsresol(options: bytes, endian: str) -> float:
    """Read the if_tsresol option (code 9). Default resolution is microseconds."""
    off = 0
    while off + 4 <= len(options):
        code, length = struct.unpack(endian + "HH", options[off : off + 4])
        off += 4
        if code == 0:  # opt_endofopt
            break
        value = options[off : off + length]
        off += length
        off += (-length) % 4  # pad to 32-bit boundary
        if code == 9 and value:
            raw = value[0]
            if raw & 0x80:
                return 2.0 ** (-(raw & 0x7F))
            return 10.0 ** (-raw)
    return 1e-6
