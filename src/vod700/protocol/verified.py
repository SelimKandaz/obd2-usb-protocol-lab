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
UPDATE_PREPARE = 0x03
UPDATE_BLOCK = 0x01
BULK_TRANSFER_SIZE = 0x1008
BULK_BODY_SIZE = 0x1000
BULK_READ_MAGIC = b"\xAA\x55\xAA\x55"
BULK_WRITE_MAGIC = b"\x55\xAA\x55\xAA"


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
class ObservedRequest:
    raw: bytes
    command: int
    checksum: int


def parse_observed_request(frame: bytes) -> ObservedRequest:
    """Validate framing/checksum while preserving any command byte.

    This is the lossless capture-facing parser. It intentionally accepts
    command bytes whose semantics are not yet known; callers that need an
    evidence-backed command should use :func:`parse_request`.
    """

    raw = _check_frame(frame, REQUEST_MAGIC)
    return ObservedRequest(raw=raw, command=raw[2], checksum=raw[CHECKSUM_OFFSET])


@dataclass(frozen=True)
class VerifiedRequest(ObservedRequest):
    address: int | None = None
    block_length: int | None = None


def parse_request(frame: bytes) -> VerifiedRequest:
    """Parse a captured interrupt OUT request with verified framing/checksum."""
    observed = parse_observed_request(frame)
    raw = observed.raw
    command = observed.command
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
class ObservedResponse:
    raw: bytes
    response_command: int
    checksum: int
    value_u32_le: int

    @property
    def request_command(self) -> int | None:
        """Return the request command for conventional ``0x80+cmd`` replies."""
        return self.response_command - 0x80 if self.response_command >= 0x80 else None


def parse_observed_response(frame: bytes) -> ObservedResponse:
    """Validate response framing/checksum without assuming command semantics."""

    raw = _check_frame(frame, RESPONSE_MAGIC)
    return ObservedResponse(
        raw=raw,
        response_command=raw[2],
        checksum=raw[CHECKSUM_OFFSET],
        value_u32_le=int.from_bytes(raw[3:7], "little"),
    )


@dataclass(frozen=True)
class VerifiedResponse(ObservedResponse):
    command: int


def parse_response(frame: bytes) -> VerifiedResponse:
    """Parse a captured interrupt IN response and its observed checksum."""
    observed = parse_observed_response(frame)
    raw = observed.raw
    response_command = observed.response_command
    if response_command not in (STORAGE_QUERY + 0x80, BLOCK_READ + 0x80):
        raise ValueError(f"unsupported evidence-backed response 0x{response_command:02X}")
    return VerifiedResponse(
        raw=raw,
        response_command=response_command,
        checksum=observed.checksum,
        value_u32_le=observed.value_u32_le,
        command=response_command - 0x80,
    )


@dataclass(frozen=True)
class UpdatePrepareObservation:
    """Captured dangerous update-prepare framing, for offline inspection only."""

    raw: bytes
    page_count: int
    checksum: int


def parse_update_prepare(frame: bytes) -> UpdatePrepareObservation:
    """Parse the observed ``0x03`` page-count frame without enabling it.

    The two bytes after command ``0x03`` are big-endian and match the ceiling
    of the selected DM100 artifact's size divided by 4 KiB in the captured
    updater path.  This parser has no live transport dependency.
    """

    raw = _check_frame(frame, REQUEST_MAGIC)
    if raw[2] != UPDATE_PREPARE:
        raise ValueError(f"expected dangerous update-prepare command 0x03, got 0x{raw[2]:02X}")
    if any(raw[5:CHECKSUM_OFFSET]):
        raise ValueError("captured 0x03 frame has non-zero reserved bytes")
    return UpdatePrepareObservation(
        raw=raw,
        page_count=int.from_bytes(raw[3:5], "big"),
        checksum=raw[CHECKSUM_OFFSET],
    )


@dataclass(frozen=True)
class UpdateBlockObservation:
    """Captured dangerous ``0x01`` block-handshake framing, offline only."""

    raw: bytes
    block_size: int
    checksum: int


def parse_update_block(frame: bytes) -> UpdateBlockObservation:
    """Parse the observed ``0x01`` full-4KiB block handshake without enabling it."""

    raw = _check_frame(frame, REQUEST_MAGIC)
    if raw[2] != UPDATE_BLOCK:
        raise ValueError(f"expected dangerous update-block command 0x01, got 0x{raw[2]:02X}")
    if any(raw[5:CHECKSUM_OFFSET]):
        raise ValueError("captured 0x01 frame has non-zero reserved bytes")
    return UpdateBlockObservation(
        raw=raw,
        block_size=int.from_bytes(raw[3:5], "big"),
        checksum=raw[CHECKSUM_OFFSET],
    )


def classify_bulk_in(payload: bytes) -> str:
    """Classify only the exact bulk-IN patterns seen in the canonical capture."""
    if len(payload) == 4096 and payload[:4] == b"\xAA\x55\xAA\x55" and set(payload[4:]) == {0xFF}:
        return "4096-byte-aa55aa55-ff-fill"
    if payload == bytes.fromhex("ffffffff000ff1fe"):
        return "8-byte-ffffffff000ff1fe-trailer"
    return "unknown"


@dataclass(frozen=True)
class BulkReadObservation:
    """Lossless metadata for the captured 4 KiB bulk-IN response layout.

    This is an offline parser only.  It proves the layout of the captured
    response, not that arbitrary ``0x06`` requests are safe to dispatch.
    """

    raw_length: int
    prefix: bytes
    data: bytes
    trailing_sum32_be: int
    calculated_sum32: int
    checksum_valid: bool
    data_sha256: str


def reassemble_bulk_read_fragments(fragments: tuple[bytes, ...] | list[bytes]) -> bytes:
    """Reassemble the exact 4,096-byte + 8-byte capture split.

    USBPcap recorded each observed logical bulk-IN frame as a 4,096-byte
    completion followed by an 8-byte completion.  The updater's static worker
    requests one ``0x1008``-byte buffer.  This helper only joins those already
    captured fragments and rejects all other shapes.
    """

    if tuple(map(len, fragments)) != (4096, 8):
        raise ValueError("captured bulk-read fragments must be exactly 4096 bytes then 8 bytes")
    return b"".join(fragments)


def inspect_bulk_read(payload: bytes) -> BulkReadObservation:
    """Validate the capture-verified ``AA55AA55 + 4KiB + SUM32-BE`` layout."""

    if len(payload) != BULK_TRANSFER_SIZE:
        raise ValueError(f"bulk read observation must be exactly {BULK_TRANSFER_SIZE} bytes")
    if payload[:4] != BULK_READ_MAGIC:
        raise ValueError(f"unexpected bulk-IN magic: {payload[:4].hex()}")
    data = payload[4:-4]
    trailing = int.from_bytes(payload[-4:], "big")
    calculated = sum(payload[:-4]) & 0xFFFFFFFF
    return BulkReadObservation(
        raw_length=len(payload),
        prefix=payload[:4],
        data=data,
        trailing_sum32_be=trailing,
        calculated_sum32=calculated,
        checksum_valid=trailing == calculated,
        data_sha256=sha256(data).hexdigest(),
    )


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
    data_sha256: str


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
        data_sha256=sha256(payload[4:-4]).hexdigest(),
    )
