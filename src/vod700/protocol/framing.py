"""Framing helpers and differential-analysis primitives.

These functions do **not** assume a header format. They provide the raw material
for forming hypotheses (constant prefixes = magic candidates, incrementing
columns = sequence-number candidates) and a way to apply a proposed layout while
keeping every unexplained byte visible.
"""
from __future__ import annotations

from collections.abc import Sequence

from .models import Field, ParsedFrame

# The interrupt endpoints report a 16-byte max packet size; the bulk endpoints
# report 64. These are VERIFIED sizes, used only as default slice widths.
INTERRUPT_FRAME_SIZE = 16
BULK_FRAME_SIZE = 64


def split_fixed(payload: bytes, size: int) -> list[bytes]:
    """Split a payload into fixed-size frames; a trailing short frame is kept."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [payload[i : i + size] for i in range(0, len(payload), size)] or [b""]


def reassemble_bulk(payloads: Sequence[bytes], packet_size: int = BULK_FRAME_SIZE) -> list[bytes]:
    """Reassemble bulk transfers under the standard short-packet-terminates rule.

    HYPOTHESIS (LOW confidence): a logical message spans consecutive max-size
    (``packet_size``) packets and ends at the first short packet. This mirrors
    common USB bulk conventions but must be confirmed against real captures.
    """
    messages: list[bytes] = []
    current = bytearray()
    for chunk in payloads:
        current += chunk
        if len(chunk) < packet_size:
            messages.append(bytes(current))
            current = bytearray()
    if current:
        messages.append(bytes(current))
    return messages


def common_prefix(frames: Sequence[bytes]) -> bytes:
    """Longest byte prefix shared by all frames (magic / fixed-header candidate)."""
    if not frames:
        return b""
    shortest = min(len(f) for f in frames)
    prefix = bytearray()
    for i in range(shortest):
        col = {f[i] for f in frames}
        if len(col) == 1:
            prefix.append(next(iter(col)))
        else:
            break
    return bytes(prefix)


def common_suffix(frames: Sequence[bytes]) -> bytes:
    if not frames:
        return b""
    shortest = min(len(f) for f in frames)
    suffix = bytearray()
    for i in range(1, shortest + 1):
        col = {f[-i] for f in frames}
        if len(col) == 1:
            suffix.append(next(iter(col)))
        else:
            break
    return bytes(reversed(suffix))


def constant_offsets(frames: Sequence[bytes]) -> dict[int, int]:
    """Byte offsets that hold the same value in every frame."""
    if not frames:
        return {}
    shortest = min(len(f) for f in frames)
    out: dict[int, int] = {}
    for i in range(shortest):
        col = {f[i] for f in frames}
        if len(col) == 1:
            out[i] = next(iter(col))
    return out


def incrementing_offsets(frames: Sequence[bytes], step: int = 1) -> list[int]:
    """Offsets whose value increments by ``step`` (mod 256) across the sequence.

    Sequence-number candidate detector. Requires at least two frames.
    """
    if len(frames) < 2:
        return []
    shortest = min(len(f) for f in frames)
    hits: list[int] = []
    for i in range(shortest):
        ok = True
        for a, b in zip(frames, frames[1:], strict=False):
            if (a[i] + step) & 0xFF != b[i]:
                ok = False
                break
        if ok:
            hits.append(i)
    return hits


def apply_layout(frame: bytes, layout: Sequence[tuple[str, int]]) -> ParsedFrame:
    """Slice ``frame`` according to ``layout`` = ``[(name, length), ...]``.

    A length of ``-1`` consumes the remainder. Any bytes beyond the layout are
    preserved as a trailing ``unknown`` field so nothing is silently dropped.
    """
    fields: list[Field] = []
    offset = 0
    for name, length in layout:
        if length < 0:
            length = len(frame) - offset
        chunk = frame[offset : offset + length]
        value: int | bytes = int.from_bytes(chunk, "little") if 0 < len(chunk) <= 4 else chunk
        fields.append(Field(name=name, offset=offset, length=len(chunk), raw=chunk, value=value))
        offset += len(chunk)
        if offset >= len(frame):
            break
    if offset < len(frame):
        rest = frame[offset:]
        fields.append(Field(name="unknown", offset=offset, length=len(rest), raw=rest, value=rest))
    return ParsedFrame(raw=frame, fields=fields, note="layout applied (hypothesis)")


def honest_parse(frame: bytes) -> ParsedFrame:
    """Default parse used when no layout is trusted yet: everything is unknown."""
    if not frame:
        return ParsedFrame(raw=frame, fields=[], note="empty frame")
    return ParsedFrame(
        raw=frame,
        fields=[Field("unknown", 0, len(frame), frame, frame)],
        note="no trusted layout; all bytes unexplained",
    )
