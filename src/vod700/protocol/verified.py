"""Evidence-backed, offline protocol lenses for the first updater exchange.

These helpers only parse captured bytes and build byte-identical request
templates observed in the official updater capture.  They do not open USB,
write endpoints, or promote any command through the safety policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .checksums import sum8

FRAME_SIZE = 16
REQUEST_MAGIC = b"\x55\xAA"
RESPONSE_MAGIC = b"\xAA\x55"
CHECKSUM_OFFSET = 15
STORAGE_QUERY = 0x0B
BLOCK_READ = 0x06


def _check_frame(frame: bytes, magic: bytes) -> bytes:
    if len(frame) != FRAME_SIZE:
        raise ValueError(f"interrupt frame must be exactly {FRAME_SIZE} bytes")
    if frame[:2] != magic:
        raise ValueError(f"unexpected frame magic: {frame[:2].hex()}")
    expected = sum8(frame[:CHECKSUM_OFFSET])
    if frame[CHECKSUM_OFFSET] != expected:
        raise ValueError(
            f"invalid additive checksum: got 0x{frame[CHECKSUM_OFFSET]:02X}, "
            f"expected 0x{expected:02X}"
        )
    return frame


def build_storage_query() -> bytes:
    """Build the captured 0x0B 16-byte request template (offline only)."""
    frame = bytearray(FRAME_SIZE)
    frame[:2] = REQUEST_MAGIC
    frame[2] = STORAGE_QUERY
    frame[CHECKSUM_OFFSET] = sum8(bytes(frame[:CHECKSUM_OFFSET]))
    return bytes(frame)


def build_block_read(address: int, block_length: int = 0x10) -> bytes:
    """Build the captured 0x06 address/length request template (offline only)."""
    if not 0 <= address <= 0xFFFFFFFF:
        raise ValueError("address must fit in an unsigned 32-bit little-endian field")
    if not 0 <= block_length <= 0xFF:
        raise ValueError("block_length must fit in one byte")
    frame = bytearray(FRAME_SIZE)
    frame[:2] = REQUEST_MAGIC
    frame[2] = BLOCK_READ
    frame[3:7] = address.to_bytes(4, "little")
    frame[8] = block_length
    frame[CHECKSUM_OFFSET] = sum8(bytes(frame[:CHECKSUM_OFFSET]))
    return bytes(frame)


@dataclass(frozen=True)
class VerifiedRequest:
    raw: bytes
    command: int
    checksum: int
    address: int | None = None
    block_length: int | None = None


def parse_request(frame: bytes) -> VerifiedRequest:
    """Parse a captured interrupt OUT request with verified framing/checksum."""
    raw = _check_frame(frame, REQUEST_MAGIC)
    command = raw[2]
    if command not in (STORAGE_QUERY, BLOCK_READ):
        raise ValueError(f"unsupported evidence-backed request command 0x{command:02X}")
    if command == STORAGE_QUERY and any(raw[3:CHECKSUM_OFFSET]):
        raise ValueError("captured 0x0B template has non-zero reserved bytes")
    if command == BLOCK_READ and (raw[7] != 0 or any(raw[9:CHECKSUM_OFFSET])):
        raise ValueError("captured 0x06 template has non-zero reserved bytes")
    return VerifiedRequest(
        raw=raw,
        command=command,
        checksum=raw[CHECKSUM_OFFSET],
        address=int.from_bytes(raw[3:7], "little") if command == BLOCK_READ else None,
        block_length=raw[8] if command == BLOCK_READ else None,
    )


@dataclass(frozen=True)
class VerifiedResponse:
    raw: bytes
    response_command: int
    command: int
    checksum: int
    value_u32_le: int


def parse_response(frame: bytes) -> VerifiedResponse:
    """Parse a captured interrupt IN response and its observed checksum."""
    raw = _check_frame(frame, RESPONSE_MAGIC)
    response_command = raw[2]
    if response_command not in (STORAGE_QUERY + 0x80, BLOCK_READ + 0x80):
        raise ValueError(f"unsupported evidence-backed response 0x{response_command:02X}")
    return VerifiedResponse(
        raw=raw,
        response_command=response_command,
        command=response_command - 0x80,
        checksum=raw[CHECKSUM_OFFSET],
        value_u32_le=int.from_bytes(raw[3:7], "little"),
    )


def classify_bulk_in(payload: bytes) -> str:
    """Classify only the exact bulk-IN patterns seen in the canonical capture."""
    if len(payload) == 4096 and payload[:4] == b"\xAA\x55\xAA\x55" and set(payload[4:]) == {0xFF}:
        return "4096-byte-aa55aa55-ff-fill"
    if payload == bytes.fromhex("ffffffff000ff1fe"):
        return "8-byte-ffffffff000ff1fe-trailer"
    return "unknown"


@dataclass(frozen=True)
class BulkWriteObservation:
    """Metadata for a captured bulk-OUT block; never a transmit builder."""

    raw_length: int
    prefix: bytes
    body_length: int
    trailing_sum32_be: int
    calculated_sum32: int
    checksum_valid: bool
    payload_sha256: str


def inspect_bulk_write(payload: bytes) -> BulkWriteObservation:
    """Inspect the observed 0x1008-byte bulk-OUT layout without enabling writes."""
    if len(payload) < 8:
        raise ValueError("bulk write observation is too short")
    prefix = payload[:4]
    body = payload[:-4]
    trailing = int.from_bytes(payload[-4:], "big")
    calculated = sum(body) & 0xFFFFFFFF
    return BulkWriteObservation(
        raw_length=len(payload),
        prefix=prefix,
        body_length=len(body),
        trailing_sum32_be=trailing,
        calculated_sum32=calculated,
        checksum_valid=trailing == calculated,
        payload_sha256=sha256(payload).hexdigest(),
    )
