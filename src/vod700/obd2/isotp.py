"""ISO-TP (ISO 15765-2) framing and reassembly for offline CAN data."""
from __future__ import annotations

from dataclasses import dataclass

from .frames import CanFrame


class IsoTpError(ValueError):
    """Raised for malformed or out-of-order ISO-TP frames."""


@dataclass(frozen=True, slots=True)
class FlowControl:
    """Decoded ISO-TP flow-control metadata."""

    status: int
    block_size: int
    separation_time: int

    @property
    def status_name(self) -> str:
        return {0: "CTS", 1: "WAIT", 2: "OVERFLOW"}.get(self.status, "UNKNOWN")


def _padded(data: bytes, pad: int) -> bytes:
    if not 0 <= pad <= 0xFF:
        raise IsoTpError("padding byte must fit one byte")
    return data + bytes([pad]) * (8 - len(data))


def encode_single_frame(
    payload: bytes, arbitration_id: int, *, pad: int = 0x00, extended: bool = False
) -> CanFrame:
    """Build one classical-CAN ISO-TP single frame in memory.

    A single frame carries at most seven payload bytes. The returned frame is
    padded to eight bytes, as is conventional for OBD-II CAN fixtures.
    """

    payload = bytes(payload)
    if not payload or len(payload) > 7:
        raise IsoTpError("single-frame payload must contain 1..7 bytes")
    return CanFrame(arbitration_id, _padded(bytes([len(payload)]) + payload, pad), extended)


def encode_isotp(
    payload: bytes, arbitration_id: int, *, pad: int = 0x00, extended: bool = False
) -> list[CanFrame]:
    """Fragment a payload into classical-CAN ISO-TP frames.

    This is a pure builder for fixtures. It does not implement flow-control
    timing and never transmits the returned frames.
    """

    payload = bytes(payload)
    if not payload:
        raise IsoTpError("ISO-TP payload must not be empty")
    if len(payload) <= 7:
        return [encode_single_frame(payload, arbitration_id, pad=pad, extended=extended)]
    if len(payload) > 0xFFF:
        raise IsoTpError("classical ISO-TP payload must fit the 12-bit length field")
    first = bytes([0x10 | ((len(payload) >> 8) & 0x0F), len(payload) & 0xFF]) + payload[:6]
    frames = [CanFrame(arbitration_id, _padded(first, pad), extended)]
    sequence = 1
    offset = 6
    while offset < len(payload):
        chunk = payload[offset : offset + 7]
        frames.append(CanFrame(arbitration_id, _padded(bytes([0x20 | sequence]) + chunk, pad), extended))
        sequence = (sequence + 1) & 0x0F
        offset += len(chunk)
    return frames


def parse_flow_control(frame: CanFrame) -> FlowControl:
    """Decode a flow-control frame without applying timing or sending it."""

    if not frame.data or frame.data[0] >> 4 != 0x3:
        raise IsoTpError("frame is not an ISO-TP flow-control frame")
    if len(frame.data) < 3:
        raise IsoTpError("flow-control frame must contain at least three bytes")
    return FlowControl(frame.data[0] & 0x0F, frame.data[1], frame.data[2])


class IsoTpReassembler:
    """Reassemble one ISO-TP message from ordered CAN frames.

    ``feed`` returns a complete payload for a single/last frame and ``None``
    while a multi-frame message is incomplete. A new first frame starts a new
    message. Flow-control frames are rejected because this class is a passive
    response parser, not a transport scheduler.
    """

    def __init__(self) -> None:
        self._expected: int | None = None
        self._buffer = bytearray()
        self._next_sequence = 1
        self._arbitration_id: int | None = None

    def reset(self) -> None:
        self._expected = None
        self._buffer.clear()
        self._next_sequence = 1
        self._arbitration_id = None

    def feed(self, frame: CanFrame) -> bytes | None:
        if not frame.data:
            raise IsoTpError("ISO-TP frame has no PCI byte")
        pci_type = frame.data[0] >> 4
        if pci_type == 0x0:
            length = frame.data[0] & 0x0F
            if length == 0 or length > len(frame.data) - 1:
                raise IsoTpError("invalid single-frame payload length")
            self.reset()
            return bytes(frame.data[1 : 1 + length])
        if pci_type == 0x1:
            if len(frame.data) < 2:
                raise IsoTpError("first frame must contain a length field")
            expected = ((frame.data[0] & 0x0F) << 8) | frame.data[1]
            if expected <= 7:
                raise IsoTpError("first-frame length must exceed single-frame capacity")
            initial = frame.data[2:]
            if len(initial) >= expected:
                raise IsoTpError("first frame unexpectedly contains complete payload")
            self._expected = expected
            self._buffer = bytearray(initial)
            self._next_sequence = 1
            self._arbitration_id = frame.arbitration_id
            return None
        if pci_type == 0x2:
            if self._expected is None:
                raise IsoTpError("consecutive frame received without a first frame")
            if frame.arbitration_id != self._arbitration_id:
                raise IsoTpError("consecutive frame arbitration ID changed")
            sequence = frame.data[0] & 0x0F
            if sequence != self._next_sequence:
                raise IsoTpError(
                    f"unexpected consecutive-frame sequence {sequence}; "
                    f"expected {self._next_sequence}"
                )
            self._buffer.extend(frame.data[1:])
            self._next_sequence = (self._next_sequence + 1) & 0x0F
            if len(self._buffer) < self._expected:
                return None
            if len(self._buffer) > self._expected:
                payload = bytes(self._buffer[: self._expected])
            else:
                payload = bytes(self._buffer)
            self.reset()
            return payload
        if pci_type == 0x3:
            raise IsoTpError("flow-control frames are not response payloads")
        raise IsoTpError(f"unsupported ISO-TP PCI type 0x{pci_type:X}")
