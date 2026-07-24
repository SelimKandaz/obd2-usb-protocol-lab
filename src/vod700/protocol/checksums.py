"""Checksum / CRC candidate algorithms and a multi-frame consistency detector.

Methodology note: a checksum algorithm is *never* declared from a single frame.
:func:`analyze_trailing` requires that a candidate reproduce the trailing bytes
of **every** supplied frame (and at least ``min_frames`` of them) before it is
reported as consistent.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass


def _reflect(value: int, width: int) -> int:
    result = 0
    for i in range(width):
        if value & (1 << i):
            result |= 1 << (width - 1 - i)
    return result


# --- Simple (non-CRC) checksums -------------------------------------------
def sum8(data: bytes) -> int:
    return sum(data) & 0xFF


def sum8_twos_complement(data: bytes) -> int:
    """Checksum such that (sum(body) + checksum) & 0xFF == 0."""
    return (-sum(data)) & 0xFF


def sum8_ones_complement(data: bytes) -> int:
    return (~sum(data)) & 0xFF


def xor8(data: bytes) -> int:
    acc = 0
    for b in data:
        acc ^= b
    return acc


def sum16_le(data: bytes) -> int:
    return sum(data) & 0xFFFF


def sum16_be(data: bytes) -> int:  # identical value; endianness only matters on read
    return sum(data) & 0xFFFF


# --- Generic CRC engines ---------------------------------------------------
def crc8(
    data: bytes,
    poly: int = 0x07,
    init: int = 0x00,
    refin: bool = False,
    refout: bool = False,
    xorout: int = 0x00,
) -> int:
    crc = init
    for byte in data:
        b = _reflect(byte, 8) if refin else byte
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    if refout:
        crc = _reflect(crc, 8)
    return crc ^ xorout


def crc16(
    data: bytes,
    poly: int = 0x1021,
    init: int = 0xFFFF,
    refin: bool = False,
    refout: bool = False,
    xorout: int = 0x0000,
) -> int:
    crc = init
    for byte in data:
        b = _reflect(byte, 8) if refin else byte
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    if refout:
        crc = _reflect(crc, 16)
    return crc ^ xorout


# --- Named registries (parameters from the well-known CRC catalogue) -------
Algorithm = Callable[[bytes], int]

SIMPLE_8: dict[str, Algorithm] = {
    "SUM8": sum8,
    "SUM8_TWOS_COMPLEMENT": sum8_twos_complement,
    "SUM8_ONES_COMPLEMENT": sum8_ones_complement,
    "XOR8": xor8,
}

CRC_8: dict[str, Algorithm] = {
    "CRC-8/SMBUS": lambda d: crc8(d, 0x07, 0x00, False, False, 0x00),
    "CRC-8/ROHC": lambda d: crc8(d, 0x07, 0xFF, True, True, 0x00),
    "CRC-8/ITU": lambda d: crc8(d, 0x07, 0x00, False, False, 0x55),
    "CRC-8/MAXIM-DOW": lambda d: crc8(d, 0x31, 0x00, True, True, 0x00),
    "CRC-8/DARC": lambda d: crc8(d, 0x39, 0x00, True, True, 0x00),
    "CRC-8/NRSC-5": lambda d: crc8(d, 0x31, 0xFF, False, False, 0x00),
    "CRC-8/BLUETOOTH": lambda d: crc8(d, 0xA7, 0x00, True, True, 0x00),
}

CRC_16: dict[str, Algorithm] = {
    "CRC-16/CCITT-FALSE": lambda d: crc16(d, 0x1021, 0xFFFF, False, False, 0x0000),
    "CRC-16/XMODEM": lambda d: crc16(d, 0x1021, 0x0000, False, False, 0x0000),
    "CRC-16/KERMIT": lambda d: crc16(d, 0x1021, 0x0000, True, True, 0x0000),
    "CRC-16/ARC": lambda d: crc16(d, 0x8005, 0x0000, True, True, 0x0000),
    "CRC-16/MODBUS": lambda d: crc16(d, 0x8005, 0xFFFF, True, True, 0x0000),
    "CRC-16/USB": lambda d: crc16(d, 0x8005, 0xFFFF, True, True, 0xFFFF),
    "CRC-16/MAXIM": lambda d: crc16(d, 0x8005, 0x0000, True, True, 0xFFFF),
    "CRC-16/GENIBUS": lambda d: crc16(d, 0x1021, 0xFFFF, False, False, 0xFFFF),
}


@dataclass
class ChecksumCandidate:
    name: str
    width_bits: int
    matches: int
    total: int
    endian: str = ""

    @property
    def consistent(self) -> bool:
        return self.total > 0 and self.matches == self.total

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "width_bits": self.width_bits,
            "endian": self.endian,
            "matches": self.matches,
            "total": self.total,
            "consistent": self.consistent,
        }


def analyze_trailing(
    frames: Sequence[bytes],
    *,
    min_frames: int = 2,
    include_8: bool = True,
    include_16: bool = True,
) -> tuple[list[ChecksumCandidate], list[ChecksumCandidate]]:
    """Hypothesis: the checksum is the last 1 (or 2) bytes of each frame.

    Returns ``(all_candidates, consistent_candidates)`` where a *consistent*
    candidate reproduces the trailing bytes of every eligible frame and there
    are at least ``min_frames`` such frames.
    """
    results: list[ChecksumCandidate] = []

    if include_8:
        for name, fn in {**SIMPLE_8, **CRC_8}.items():
            matches = total = 0
            for frame in frames:
                if len(frame) < 2:
                    continue
                total += 1
                if fn(frame[:-1]) == frame[-1]:
                    matches += 1
            results.append(ChecksumCandidate(name, 8, matches, total))

    if include_16:
        for name, fn in CRC_16.items():
            for endian in ("little", "big"):
                matches = total = 0
                for frame in frames:
                    if len(frame) < 3:
                        continue
                    total += 1
                    expected = int.from_bytes(frame[-2:], endian)
                    if fn(frame[:-2]) == expected:
                        matches += 1
                results.append(ChecksumCandidate(name, 16, matches, total, endian))

    consistent = [c for c in results if c.total >= min_frames and c.consistent]
    consistent.sort(key=lambda c: (-c.total, c.name))
    return results, consistent


def analyze_field(
    bodies: Sequence[bytes],
    checksums: Sequence[int],
    *,
    min_frames: int = 2,
    width_bits: int = 8,
) -> list[ChecksumCandidate]:
    """Like :func:`analyze_trailing` but with body and checksum supplied separately.

    Useful when the checksum is *not* the final byte (e.g. mid-frame), so the
    caller extracts ``bodies`` and ``checksums`` explicitly.
    """
    if len(bodies) != len(checksums):
        raise ValueError("bodies and checksums must be the same length")
    registry = {**SIMPLE_8, **CRC_8} if width_bits == 8 else CRC_16
    out: list[ChecksumCandidate] = []
    for name, fn in registry.items():
        matches = sum(1 for body, chk in zip(bodies, checksums, strict=True) if fn(body) == chk)
        out.append(ChecksumCandidate(name, width_bits, matches, len(bodies)))
    return [c for c in out if c.total >= min_frames and c.consistent]
