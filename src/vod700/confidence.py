"""Confidence taxonomy used across the whole project.

Every claim about the protocol carries an explicit confidence level so that
VERIFIED facts are never confused with hypotheses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Confidence(StrEnum):
    """Ordered confidence levels; compare with :meth:`at_least`."""

    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

    @property
    def rank(self) -> int:
        order = ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "VERIFIED"]
        return order.index(self.value)

    def at_least(self, other: Confidence) -> bool:
        return self.rank >= other.rank


@dataclass(frozen=True)
class Evidence:
    """A single, attributable observation backing a claim."""

    claim: str
    confidence: Confidence
    sources: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "claim": self.claim,
            "confidence": self.confidence.value,
            "sources": list(self.sources),
            "notes": self.notes,
        }


@dataclass
class EvidenceLog:
    """An append-only collection of :class:`Evidence` records."""

    entries: list[Evidence] = field(default_factory=list)

    def add(
        self,
        claim: str,
        confidence: Confidence,
        sources: tuple[str, ...] = (),
        notes: str = "",
    ) -> Evidence:
        ev = Evidence(claim, confidence, sources, notes)
        self.entries.append(ev)
        return ev

    def to_list(self) -> list[dict[str, object]]:
        return [e.to_dict() for e in self.entries]
