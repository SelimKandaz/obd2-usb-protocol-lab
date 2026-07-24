"""Turn a stream of :class:`UsbTransfer` into tentatively-interpreted messages.

Everything here is a hypothesis at LOW/UNKNOWN confidence. Roles are guessed
purely from endpoint direction and the working channel hypothesis; no byte-level
meaning is asserted. The value is structure + correlation, not conclusions.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..confidence import Confidence
from . import framing
from .models import (
    Direction,
    MessageRole,
    ParsedFrame,
    ProtocolMessage,
    TransferType,
    UsbTransfer,
)

# Working channel hypothesis (UNVERIFIED, from the project brief):
#   0x01 OUT / 0x81 IN  interrupt  = command / status / ACK
#   0x02 OUT / 0x82 IN  bulk       = data / file / firmware transfer
COMMAND_OUT_EP = 0x01
STATUS_IN_EP = 0x81
BULK_OUT_EP = 0x02
BULK_IN_EP = 0x82


def _guess_role(t: UsbTransfer) -> tuple[MessageRole, Confidence, str]:
    if t.transfer_type is TransferType.INTERRUPT:
        if t.endpoint == COMMAND_OUT_EP:
            return MessageRole.COMMAND, Confidence.LOW, "OUT on interrupt cmd-channel (hypothesis)"
        if t.endpoint == STATUS_IN_EP:
            return MessageRole.RESPONSE, Confidence.LOW, "IN on interrupt status-channel (hypothesis)"
    if t.transfer_type is TransferType.BULK:
        return MessageRole.DATA, Confidence.LOW, "bulk data-channel (hypothesis)"
    return MessageRole.UNKNOWN, Confidence.UNKNOWN, ""


def to_message(t: UsbTransfer) -> ProtocolMessage:
    """Wrap a single transfer, splitting into fixed frames where the size is known."""
    if t.transfer_type is TransferType.INTERRUPT:
        frame_bytes = t.payload[: framing.INTERRUPT_FRAME_SIZE]
    else:
        frame_bytes = t.payload
    frame: ParsedFrame = framing.honest_parse(frame_bytes)
    role, conf, note = _guess_role(t)
    return ProtocolMessage(transfer=t, frame=frame, role=role, confidence=conf, notes=note)


def to_messages(transfers: Sequence[UsbTransfer]) -> list[ProtocolMessage]:
    return [to_message(t) for t in transfers]


@dataclass
class Correlation:
    command: ProtocolMessage
    response: ProtocolMessage | None
    delay_s: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "command_index": self.command.transfer.index,
            "response_index": self.response.transfer.index if self.response else None,
            "delay_s": self.delay_s,
            "command_hex": self.command.transfer.payload_hex,
            "response_hex": self.response.transfer.payload_hex if self.response else None,
        }


def correlate_interrupt(messages: Sequence[ProtocolMessage]) -> list[Correlation]:
    """Pair each interrupt OUT command with the next interrupt IN response.

    HYPOTHESIS (LOW): request/response on the interrupt channel is strictly
    ordered. Reported delays help test that assumption against real timing.
    """
    pairs: list[Correlation] = []
    pending: ProtocolMessage | None = None
    for m in messages:
        t = m.transfer
        if t.transfer_type is not TransferType.INTERRUPT:
            continue
        if t.direction is Direction.OUT and t.endpoint == COMMAND_OUT_EP:
            if pending is not None:
                pairs.append(Correlation(pending, None, None))
            pending = m
        elif t.direction is Direction.IN and t.endpoint == STATUS_IN_EP and pending is not None:
            delay = t.timestamp - pending.transfer.timestamp
            pairs.append(Correlation(pending, m, delay))
            pending = None
    if pending is not None:
        pairs.append(Correlation(pending, None, None))
    return pairs


def repeated_payloads(messages: Sequence[ProtocolMessage]) -> dict[str, int]:
    """Count identical payloads per endpoint (heartbeat / polling candidates)."""
    counts: dict[str, int] = {}
    for m in messages:
        key = f"0x{m.transfer.endpoint:02X}:{m.transfer.payload_hex}"
        counts[key] = counts.get(key, 0) + 1
    return {k: v for k, v in counts.items() if v > 1}
