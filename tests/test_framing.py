from __future__ import annotations

from vod700.protocol import framing


def test_split_fixed():
    assert framing.split_fixed(b"\x00" * 20, 16) == [b"\x00" * 16, b"\x00" * 4]
    assert framing.split_fixed(b"", 16) == [b""]


def test_common_prefix_and_suffix():
    frames = [b"\xaa\x01\x10\x0f", b"\xaa\x02\x20\x0f", b"\xaa\x03\x30\x0f"]
    assert framing.common_prefix(frames) == b"\xaa"
    assert framing.common_suffix(frames) == b"\x0f"


def test_constant_and_incrementing_offsets():
    frames = [b"\xaa\x00\x05", b"\xaa\x01\x05", b"\xaa\x02\x05"]
    consts = framing.constant_offsets(frames)
    assert consts[0] == 0xAA and consts[2] == 0x05
    assert framing.incrementing_offsets(frames) == [1]


def test_apply_layout_preserves_unknown_tail():
    frame = b"\xaa\x12\x34\x99\xff\xee"
    parsed = framing.apply_layout(frame, [("magic", 1), ("cmd", 1), ("seq", 1)])
    names = [f.name for f in parsed.fields]
    assert names == ["magic", "cmd", "seq", "unknown"]
    assert parsed.fields[-1].raw == b"\x99\xff\xee"
    # Nothing is ever dropped.
    assert b"".join(f.raw for f in parsed.fields) == frame


def test_honest_parse_marks_everything_unknown():
    parsed = framing.honest_parse(b"\x01\x02\x03")
    assert parsed.coverage() == 0.0
    assert parsed.unexplained_bytes() == b"\x01\x02\x03"


def test_reassemble_bulk_short_packet_terminates():
    p64 = bytes(range(64))
    tail = b"\xff\xff"
    msgs = framing.reassemble_bulk([p64, tail], packet_size=64)
    assert msgs == [p64 + tail]
