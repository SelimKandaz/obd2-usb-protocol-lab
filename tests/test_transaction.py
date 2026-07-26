from vod700.client.policy import REGISTRY, SafetyClass
from vod700.client.transaction import TransactionError, run_storage_query
from vod700.mock.replay import ReplayDevice


def test_storage_query_replay_path_when_explicitly_enabled():
    spec = REGISTRY["storage_query"]
    previous = spec.enabled
    previous_safety = spec.safety
    spec.enabled = True
    spec.safety = SafetyClass.READ_ONLY
    try:
        response = bytes.fromhex("aa558b0000000200000000000000008c")
        replay = ReplayDevice.from_responses([response])
        result = run_storage_query(replay)
        assert result.request == bytes.fromhex("55aa0b0000000000000000000000000a")
        assert result.response.value_u32_le == 0x02000000
        assert replay.sent == [(0x01, result.request)]
    finally:
        spec.enabled = previous
        spec.safety = previous_safety


def test_storage_query_preserves_unclassified_response_bytes():
    spec = REGISTRY["storage_query"]
    previous = spec.enabled
    previous_safety = spec.safety
    spec.enabled = True
    spec.safety = SafetyClass.READ_ONLY
    try:
        # This is a validly framed/checksummed response shape, but command
        # 0x05 is not yet evidence-backed. The error must retain the bytes so
        # no retransmission is needed for later offline classification.
        response = bytes.fromhex("aa550500000000000000000000000004")
        replay = ReplayDevice.from_responses([response])
        try:
            run_storage_query(replay)
        except TransactionError as exc:
            assert "0x05" in str(exc)
            assert response.hex() in str(exc)
        else:  # pragma: no cover - assertion guard
            raise AssertionError("unclassified response unexpectedly accepted")
    finally:
        spec.enabled = previous
        spec.safety = previous_safety
