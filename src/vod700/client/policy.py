"""The safety gate for anything that would send bytes to the device.

No command reaches a vendor endpoint unless it is:
  * ``enabled`` (a human turned it on after review),
  * classified ``READ_ONLY``,
  * backed by at least one capture reference AND one static-analysis reference,
  * at confidence >= HIGH.

Standard USB descriptor reads are *not* in this registry — they are handled by
the driver as standard requests and are inherently read-only. This registry is
only for *protocol* requests we might send to the vendor-specific endpoints.

The registry ships **empty of dispatchable commands** on purpose. Placeholders
below document the intended structure and are all disabled.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..confidence import Confidence


class SafetyClass(StrEnum):
    READ_ONLY = "READ_ONLY"       # cannot change device state
    ACTIVE_QUERY = "ACTIVE_QUERY"  # sends bytes but expected read-only; needs proof
    UNSAFE = "UNSAFE"             # may change state — never auto-dispatched


class PolicyError(RuntimeError):
    """Raised when a command is not permitted to be dispatched."""


@dataclass
class CommandSpec:
    name: str
    description: str
    endpoint: int
    request: bytes | None = None
    expected_response: str = ""
    source_captures: tuple[str, ...] = ()
    source_code: tuple[str, ...] = ()
    safety: SafetyClass = SafetyClass.UNSAFE
    confidence: Confidence = Confidence.UNKNOWN
    timeout_ms: int = 1000
    max_response: int = 64
    enabled: bool = False
    notes: str = ""

    def blocking_reasons(self) -> list[str]:
        reasons: list[str] = []
        if not self.enabled:
            reasons.append("command is disabled (not yet approved for dispatch)")
        if self.safety is not SafetyClass.READ_ONLY:
            reasons.append(f"safety class is {self.safety.value}, must be READ_ONLY")
        if not self.confidence.at_least(Confidence.HIGH):
            reasons.append(f"confidence is {self.confidence.value}, must be >= HIGH")
        if not self.source_captures:
            reasons.append("no source capture reference")
        if not self.source_code:
            reasons.append("no static-analysis reference")
        return reasons

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "endpoint": f"0x{self.endpoint:02X}",
            "request_hex": self.request.hex() if self.request else None,
            "safety": self.safety.value,
            "confidence": self.confidence.value,
            "enabled": self.enabled,
            "dispatchable": not self.blocking_reasons(),
            "source_captures": list(self.source_captures),
            "source_code": list(self.source_code),
            "timeout_ms": self.timeout_ms,
            "max_response": self.max_response,
            "notes": self.notes,
        }


# Registry — every entry disabled until evidence exists. These names mirror the
# CLI verbs (`identify`, `version`) so the gate produces a clear refusal.
REGISTRY: dict[str, CommandSpec] = {
    "identify": CommandSpec(
        name="identify",
        description="Request device identity / model string (hypothetical).",
        endpoint=0x01,
        safety=SafetyClass.UNSAFE,
        confidence=Confidence.UNKNOWN,
        notes="No request bytes are known yet. Populate from handshake capture first.",
    ),
    "version": CommandSpec(
        name="version",
        description="Request firmware/application version (hypothetical).",
        endpoint=0x01,
        safety=SafetyClass.UNSAFE,
        confidence=Confidence.UNKNOWN,
        notes="No request bytes are known yet. Populate from handshake capture first.",
    ),
}


def register(spec: CommandSpec) -> None:
    REGISTRY[spec.name] = spec


def list_commands() -> list[CommandSpec]:
    return list(REGISTRY.values())


def assert_dispatchable(name: str) -> CommandSpec:
    spec = REGISTRY.get(name)
    if spec is None:
        raise PolicyError(f"unknown command: {name!r}")
    reasons = spec.blocking_reasons()
    if reasons:
        raise PolicyError(
            f"command {name!r} is not dispatchable:\n  - " + "\n  - ".join(reasons)
        )
    return spec
