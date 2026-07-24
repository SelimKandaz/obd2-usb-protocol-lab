"""A scripted replay device for developing/parsing without hardware.

Scenario kinds exercised by the test-suite: normal, timeout, truncated,
duplicate, out_of_order, nack, checksum_error, disconnect. Content-level
scenarios (nack / checksum_error / out_of_order) are represented by the response
bytes themselves; transport-level scenarios (timeout / truncated / duplicate /
disconnect) change how :meth:`ReplayDevice.read` behaves.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class MockUsbError(RuntimeError):
    pass


class DeviceDisconnected(MockUsbError):
    pass


@dataclass
class Exchange:
    endpoint: int
    response: bytes
    kind: str = "normal"  # normal|timeout|truncated|duplicate|disconnect|nack|checksum_error|out_of_order

    def to_dict(self) -> dict[str, object]:
        return {"endpoint": f"0x{self.endpoint:02X}", "kind": self.kind, "response_hex": self.response.hex()}


@dataclass
class ReplayDevice:
    """Replays a scripted list of device responses; records host writes."""

    exchanges: list[Exchange] = field(default_factory=list)
    packet_size: int = 64
    _pos: int = 0
    sent: list[tuple[int, bytes]] = field(default_factory=list)

    @classmethod
    def from_responses(cls, responses: list[bytes], endpoint: int = 0x81) -> ReplayDevice:
        return cls([Exchange(endpoint, r) for r in responses])

    def write(self, endpoint: int, data: bytes) -> int:
        """Record a host->device write. Never forwarded anywhere; this is a mock."""
        self.sent.append((endpoint, bytes(data)))
        return len(data)

    def read(self, endpoint: int = 0x81, max_len: int = 64, timeout_s: float = 1.0) -> bytes:
        if self._pos >= len(self.exchanges):
            raise TimeoutError("no more scripted responses")
        ex = self.exchanges[self._pos]
        self._pos += 1

        if ex.kind == "timeout":
            raise TimeoutError(f"scripted timeout on 0x{endpoint:02X} after {timeout_s}s")
        if ex.kind == "disconnect":
            raise DeviceDisconnected("scripted device disconnect")
        if ex.kind == "truncated":
            return ex.response[: max(1, len(ex.response) // 2)]
        if ex.kind == "duplicate":
            # Re-queue a copy so the next read returns the same bytes again.
            self.exchanges.insert(self._pos, Exchange(ex.endpoint, ex.response, "normal"))
            return ex.response[:max_len]
        return ex.response[:max_len]

    def read_all(self, endpoint: int = 0x81) -> list[bytes]:
        out: list[bytes] = []
        while self._pos < len(self.exchanges):
            try:
                out.append(self.read(endpoint))
            except (TimeoutError, DeviceDisconnected):
                break
        return out

    def remaining(self) -> int:
        return len(self.exchanges) - self._pos
