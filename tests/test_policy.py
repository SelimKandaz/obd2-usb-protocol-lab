from __future__ import annotations

import pytest

from vod700.client.policy import (
    CommandSpec,
    PolicyError,
    SafetyClass,
    assert_dispatchable,
)
from vod700.confidence import Confidence


def test_shipped_active_commands_are_all_gated():
    with pytest.raises(PolicyError):
        assert_dispatchable("identify")
    with pytest.raises(PolicyError):
        assert_dispatchable("version")


def test_unknown_command_raises():
    with pytest.raises(PolicyError):
        assert_dispatchable("does-not-exist")


def test_fully_evidenced_readonly_command_has_no_blockers():
    spec = CommandSpec(
        name="probe_ok",
        description="verified read-only request",
        endpoint=0x01,
        request=b"\x01",
        safety=SafetyClass.READ_ONLY,
        confidence=Confidence.VERIFIED,
        source_captures=("handshake.pcapng#42",),
        source_code=("Updater.dll!BuildInfoCmd",),
        enabled=True,
    )
    assert spec.blocking_reasons() == []


def test_missing_evidence_blocks_even_when_enabled():
    spec = CommandSpec(
        name="x",
        description="d",
        endpoint=0x01,
        safety=SafetyClass.READ_ONLY,
        confidence=Confidence.HIGH,
        enabled=True,
    )
    reasons = spec.blocking_reasons()
    assert any("capture" in r for r in reasons)
    assert any("static-analysis" in r for r in reasons)


def test_active_query_safety_is_blocked():
    spec = CommandSpec(
        name="y",
        description="d",
        endpoint=0x01,
        safety=SafetyClass.ACTIVE_QUERY,
        confidence=Confidence.VERIFIED,
        source_captures=("c",),
        source_code=("s",),
        enabled=True,
    )
    assert any("READ_ONLY" in r for r in spec.blocking_reasons())
