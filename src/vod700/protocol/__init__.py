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
from .verified import (
    BLOCK_READ,
    STORAGE_QUERY,
    BulkWriteObservation,
    VerifiedRequest,
    VerifiedResponse,
    build_block_read,
    build_storage_query,
    classify_bulk_in,
    inspect_bulk_write,
    parse_request,
    parse_response,
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
    "STORAGE_QUERY",
    "BLOCK_READ",
    "VerifiedRequest",
    "VerifiedResponse",
    "BulkWriteObservation",
    "build_storage_query",
    "build_block_read",
    "parse_request",
    "parse_response",
    "classify_bulk_in",
    "inspect_bulk_write",
]
