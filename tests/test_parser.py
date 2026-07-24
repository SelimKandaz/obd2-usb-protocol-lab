from __future__ import annotations

from vod700.mock.fixtures import synthetic_interrupt_transfers
from vod700.protocol.models import MessageRole
from vod700.protocol.parser import correlate_interrupt, repeated_payloads, to_messages


def test_roles_follow_channel_hypothesis():
    msgs = to_messages(synthetic_interrupt_transfers())
    out = [m for m in msgs if m.transfer.endpoint == 0x01]
    inn = [m for m in msgs if m.transfer.endpoint == 0x81]
    assert out and all(m.role == MessageRole.COMMAND for m in out)
    assert inn and all(m.role == MessageRole.RESPONSE for m in inn)


def test_correlate_interrupt_pairs_command_with_response():
    msgs = to_messages(synthetic_interrupt_transfers())
    pairs = correlate_interrupt(msgs)
    assert len(pairs) == 3
    assert all(p.response is not None for p in pairs)
    assert all(p.delay_s is not None and p.delay_s > 0 for p in pairs)


def test_repeated_payloads_detects_duplicates():
    msgs = to_messages(synthetic_interrupt_transfers())
    reps = repeated_payloads(msgs)
    # The three IN responses are identical -> at least one repeated payload key.
    assert any(count >= 2 for count in reps.values())
