"""Protocol layer: typed USB/message models, checksum detectors, framing and parsing.

Design rule: **never discard bytes.** Every parsed structure keeps the original
raw bytes, and any byte not explained by a hypothesis stays visible as an
``unknown`` field.
"""
from __future__ import annotations

from .models import (
    AckResponse,
    BulkFrame,
    DeviceInfoResponse,
    Direction,
    ErrorResponse,
    Field,
    InterruptCommand,
    InterruptResponse,
    MessageRole,
    ParsedFrame,
    ProtocolMessage,
    TransferType,
    UsbTransfer,
)

__all__ = [
    "Direction",
    "TransferType",
    "UsbTransfer",
    "Field",
    "ParsedFrame",
    "MessageRole",
    "ProtocolMessage",
    "InterruptCommand",
    "InterruptResponse",
    "BulkFrame",
    "AckResponse",
    "ErrorResponse",
    "DeviceInfoResponse",
]
