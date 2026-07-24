"""Typed models for USB transfers and (hypothesized) protocol messages.

The single most important invariant here: raw bytes are always preserved. Higher
level views (:class:`AckResponse`, :class:`DeviceInfoResponse`, ...) are *lenses*
over the same underlying bytes, never a replacement for them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ..confidence import Confidence


class Direction(StrEnum):
    IN = "IN"      # device -> host
    OUT = "OUT"    # host -> device


class TransferType(StrEnum):
    CONTROL = "CONTROL"
    ISOCHRONOUS = "ISOCHRONOUS"
    BULK = "BULK"
    INTERRUPT = "INTERRUPT"


@dataclass
class UsbTransfer:
    """One normalized USB transfer, as reconstructed from a capture.

    This is the boundary type between the capture layer and the protocol layer.
    ``payload`` is the data-stage bytes only (no USBPcap/URB pseudo-header).
    """

    index: int
    timestamp: float
    endpoint: int
    direction: Direction
    transfer_type: TransferType
    payload: bytes = b""
    bus: int = 0
    address: int = 0
    requested_length: int | None = None
    actual_length: int | None = None
    urb_function: int | None = None
    status: int | None = None
    capture_id: str = ""

    @property
    def endpoint_number(self) -> int:
        return self.endpoint & 0x0F

    @property
    def payload_hex(self) -> str:
        return self.payload.hex()

    @property
    def length(self) -> int:
        return len(self.payload)

    def endpoint_label(self) -> str:
        return f"0x{self.endpoint:02X} {self.direction.value} {self.transfer_type.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "bus": self.bus,
            "address": self.address,
            "endpoint": self.endpoint,
            "endpoint_hex": f"0x{self.endpoint:02X}",
            "direction": self.direction.value,
            "transfer_type": self.transfer_type.value,
            "urb_function": self.urb_function,
            "status": self.status,
            "requested_length": self.requested_length,
            "actual_length": self.actual_length,
            "length": self.length,
            "payload_hex": self.payload_hex,
            "capture_id": self.capture_id,
        }


@dataclass
class Field:
    """A named slice of a frame. ``raw`` always holds the exact bytes."""

    name: str
    offset: int
    length: int
    raw: bytes
    value: int | bytes | str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "offset": self.offset,
            "length": self.length,
            "raw_hex": self.raw.hex(),
            "value": self.value if isinstance(self.value, (int, str)) else (
                self.value.hex() if isinstance(self.value, bytes) else None
            ),
            "note": self.note,
        }


@dataclass
class ParsedFrame:
    """A frame decomposed into named fields, with all unexplained bytes kept.

    ``fields`` may include entries named ``"unknown"`` for byte ranges that no
    hypothesis has explained yet. :meth:`unexplained_bytes` reports how much of
    the frame remains a mystery.
    """

    raw: bytes
    fields: list[Field] = field(default_factory=list)
    note: str = ""

    def covered_offsets(self) -> set[int]:
        covered: set[int] = set()
        for f in self.fields:
            if f.name != "unknown":
                covered.update(range(f.offset, f.offset + f.length))
        return covered

    def unexplained_bytes(self) -> bytes:
        covered = self.covered_offsets()
        return bytes(self.raw[i] for i in range(len(self.raw)) if i not in covered)

    def coverage(self) -> float:
        if not self.raw:
            return 1.0
        return len(self.covered_offsets()) / len(self.raw)

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_hex": self.raw.hex(),
            "length": len(self.raw),
            "coverage": round(self.coverage(), 3),
            "unexplained_hex": self.unexplained_bytes().hex(),
            "fields": [f.to_dict() for f in self.fields],
            "note": self.note,
        }


class MessageRole(StrEnum):
    UNKNOWN = "UNKNOWN"
    COMMAND = "COMMAND"
    RESPONSE = "RESPONSE"
    ACK = "ACK"
    NACK = "NACK"
    HEARTBEAT = "HEARTBEAT"
    DEVICE_INFO = "DEVICE_INFO"
    VERSION = "VERSION"
    ERROR = "ERROR"
    DATA = "DATA"


@dataclass
class ProtocolMessage:
    """A transfer interpreted at the protocol level. Interpretation is tentative."""

    transfer: UsbTransfer
    frame: ParsedFrame
    role: MessageRole = MessageRole.UNKNOWN
    confidence: Confidence = Confidence.UNKNOWN
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "transfer": self.transfer.to_dict(),
            "frame": self.frame.to_dict(),
            "role": self.role.value,
            "confidence": self.confidence.value,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------
# Named message lenses. These exist so downstream code has stable types to
# target, but they are UNVERIFIED until capture evidence populates them. Each
# keeps the raw bytes so nothing is ever lost to a premature interpretation.
# --------------------------------------------------------------------------
@dataclass
class InterruptCommand:
    raw: bytes
    confidence: Confidence = Confidence.UNKNOWN


@dataclass
class InterruptResponse:
    raw: bytes
    confidence: Confidence = Confidence.UNKNOWN


@dataclass
class BulkFrame:
    raw: bytes
    index: int = 0
    is_final: bool = False
    confidence: Confidence = Confidence.UNKNOWN


@dataclass
class AckResponse:
    raw: bytes
    status: int | None = None
    sequence: int | None = None
    confidence: Confidence = Confidence.UNKNOWN


@dataclass
class ErrorResponse:
    raw: bytes
    code: int | None = None
    confidence: Confidence = Confidence.UNKNOWN


@dataclass
class DeviceInfoResponse:
    raw: bytes
    fields: dict[str, object] = field(default_factory=dict)
    confidence: Confidence = Confidence.UNKNOWN
