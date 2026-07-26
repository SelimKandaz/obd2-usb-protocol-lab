"""Policy-gated transaction state machine for the evidenced query path.

The transport is injected so replay/mock validation is possible without a
device. No WinUSB implementation is hidden here, and the default policy keeps
the live storage query disabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from ..protocol.verified import VerifiedResponse, build_storage_query, parse_response
from .policy import assert_dispatchable


class PipeTransport(Protocol):
    def write(self, endpoint: int, data: bytes) -> int: ...

    def read(self, endpoint: int, max_len: int, timeout_s: float) -> bytes: ...


class TransactionError(RuntimeError):
    """Raised when a gated transaction does not complete or validate."""


@dataclass(frozen=True)
class StorageQueryResult:
    request: bytes
    response: VerifiedResponse
    write_length: int
    elapsed_s: float


def run_storage_query(transport: PipeTransport) -> StorageQueryResult:
    """Run the evidenced query only when policy explicitly permits it.

    The shipped policy is disabled, so this function raises before calling the
    injected transport. Tests enable the spec temporarily on a replay device;
    no production call path enables it automatically.
    """
    spec = assert_dispatchable("storage_query")
    request = build_storage_query()
    started = monotonic()
    written = transport.write(spec.endpoint, request)
    if written != len(request):
        raise TransactionError(f"short write: {written}/{len(request)} bytes")
    raw_response = transport.read(0x81, spec.max_response, spec.timeout_ms / 1000.0)
    if len(raw_response) != spec.max_response:
        raise TransactionError(f"short response: {len(raw_response)}/{spec.max_response} bytes")
    try:
        response = parse_response(raw_response)
    except ValueError as exc:
        raise TransactionError(f"invalid storage-query response: {exc}") from exc
    if response.command != 0x0B:
        raise TransactionError(f"unexpected response command 0x{response.response_command:02X}")
    return StorageQueryResult(request, response, written, monotonic() - started)
