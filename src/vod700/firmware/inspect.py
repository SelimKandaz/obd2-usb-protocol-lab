"""Reproducible, read-only inspection for opaque update containers.

The functions in this module intentionally report structural evidence instead
of pretending that random byte signatures are embedded files.  A matching
magic value in high-entropy data is a *candidate*, and a compression stream is
only reported as valid after the standard-library decoder reaches EOF.

No output includes file bytes by default.  This keeps private updater/firmware
material out of normal reports while still recording hashes, boundaries, and
repeat statistics needed for reproducible research.
"""
from __future__ import annotations

import bz2
import lzma
import math
import struct
import zlib
from collections import Counter
from hashlib import sha256
from pathlib import Path

_MAGICS: tuple[tuple[str, bytes], ...] = (
    ("BZIP2", b"BZh"),
    ("ELF", b"\x7fELF"),
    ("GZIP", b"\x1f\x8b\x08"),
    ("LZ4_FRAME", b"\x04\x22\x4d\x18"),
    ("MZ", b"MZ"),
    ("PNG", b"\x89PNG\r\n\x1a\n"),
    ("RAR", b"Rar!\x1a\x07"),
    ("SQUASHFS_LE", b"hsqs"),
    ("XZ", b"\xfd7zXZ\x00"),
    ("ZIP", b"PK\x03\x04"),
    ("ZSTD", b"\x28\xb5\x2f\xfd"),
)


def shannon_entropy(data: bytes) -> float:
    """Return Shannon entropy in bits per byte (0.0 to 8.0)."""
    if not data:
        return 0.0
    counts = Counter(data)
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def _count_ascii_strings(data: bytes, minimum_length: int = 4) -> int:
    """Count printable ASCII runs without returning their private contents."""
    count = 0
    run = 0
    for byte in data:
        if 0x20 <= byte <= 0x7E:
            run += 1
        else:
            if run >= minimum_length:
                count += 1
            run = 0
    return count + int(run >= minimum_length)


def _magic_hits(data: bytes, maximum_per_magic: int = 8) -> list[dict[str, object]]:
    """Find byte-signature candidates, capped to avoid noisy random data."""
    hits: list[dict[str, object]] = []
    for name, magic in _MAGICS:
        offsets: list[int] = []
        start = 0
        while len(offsets) < maximum_per_magic:
            offset = data.find(magic, start)
            if offset < 0:
                break
            offsets.append(offset)
            start = offset + 1
        if offsets:
            hits.append(
                {
                    "name": name,
                    "count_capped": len(offsets) == maximum_per_magic,
                    "offsets": offsets,
                }
            )
    return hits


def _cortex_m_vector_candidates(data: bytes, maximum: int = 16) -> list[int]:
    """Locate plausible Cortex-M SP/reset pairs; each result remains a candidate.

    This deliberately uses broad common SRAM/flash ranges and must not be
    interpreted as proof of an MCU family or an executable image.
    """
    candidates: list[int] = []
    for offset in range(0, max(0, len(data) - 7), 4):
        stack_pointer, reset_vector = struct.unpack_from("<II", data, offset)
        plausible_stack = 0x20000000 <= stack_pointer <= 0x200FFFFF
        plausible_reset = 0x08000001 <= reset_vector <= 0x08200001 and reset_vector & 1
        if plausible_stack and plausible_reset:
            candidates.append(offset)
            if len(candidates) >= maximum:
                break
    return candidates


def _block_repeat_stats(data: bytes, block_size: int) -> dict[str, object]:
    blocks = [data[offset : offset + block_size] for offset in range(0, len(data) - block_size + 1, block_size)]
    counts = Counter(blocks)
    repeated_instances = sum(count - 1 for count in counts.values() if count > 1)
    tail = data[-block_size:] if len(data) >= block_size else b""
    return {
        "block_size": block_size,
        "aligned_block_count": len(blocks),
        "repeated_instances": repeated_instances,
        "maximum_same_block_count": max(counts.values(), default=0),
        "tail_sha256_16": sha256(tail).hexdigest()[:16].upper(),
        "tail_occurrences": counts[tail] if tail else 0,
    }


def _entropy_windows(data: bytes, window_size: int = 65536) -> dict[str, object]:
    if not data:
        return {"window_size": window_size, "count": 0, "minimum": 0.0, "maximum": 0.0}
    windows = [
        shannon_entropy(data[offset : offset + window_size])
        for offset in range(0, len(data), window_size)
    ]
    minimum_index = min(range(len(windows)), key=windows.__getitem__)
    maximum_index = max(range(len(windows)), key=windows.__getitem__)
    return {
        "window_size": window_size,
        "count": len(windows),
        "minimum": round(windows[minimum_index], 6),
        "minimum_offset": minimum_index * window_size,
        "maximum": round(windows[maximum_index], 6),
        "maximum_offset": maximum_index * window_size,
    }


def _stream_metadata(
    *,
    offset: int,
    source: bytes,
    decoded: bytes,
    unused: bytes,
) -> dict[str, object]:
    """Return metadata after a standard decoder reached end-of-stream."""

    return {
        "offset": offset,
        "compressed_length": len(source) - len(unused),
        "decoded_length": len(decoded),
        "decoded_sha256_16": sha256(decoded).hexdigest()[:16].upper(),
    }


def _valid_zlib_streams(data: bytes, maximum_output: int = 16 * 1024 * 1024) -> list[dict[str, object]]:
    """Return verified zlib streams without retaining decoded private bytes.

    Random high-entropy input often contains zlib-looking two-byte values.  A
    candidate is listed only when ``zlib.decompressobj`` consumes a complete
    stream and reaches EOF.  The decoded data is discarded after hashing.
    """
    streams: list[dict[str, object]] = []
    search_from = 0
    while True:
        offset = data.find(b"\x78", search_from)
        if offset < 0:
            break
        search_from = offset + 1
        if offset + 2 > len(data):
            continue
        cmf, flg = data[offset], data[offset + 1]
        if (cmf & 0x0F) != 8 or ((cmf << 8) + flg) % 31:
            continue
        try:
            decoder = zlib.decompressobj()
            decoded = decoder.decompress(data[offset:], maximum_output)
        except zlib.error:
            continue
        if not decoder.eof:
            continue
        streams.append(
            _stream_metadata(
                offset=offset,
                source=data[offset:],
                decoded=decoded,
                unused=decoder.unused_data,
            )
        )
    return streams


def _valid_gzip_streams(data: bytes, maximum_output: int = 16 * 1024 * 1024) -> list[dict[str, object]]:
    """Validate gzip candidates rather than treating the three-byte magic as proof."""

    streams: list[dict[str, object]] = []
    search_from = 0
    while True:
        offset = data.find(b"\x1f\x8b\x08", search_from)
        if offset < 0:
            return streams
        search_from = offset + 1
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        try:
            decoded = decoder.decompress(data[offset:], maximum_output)
        except zlib.error:
            continue
        if decoder.eof:
            streams.append(
                _stream_metadata(
                    offset=offset,
                    source=data[offset:],
                    decoded=decoded,
                    unused=decoder.unused_data,
                )
            )


def _valid_bz2_streams(data: bytes, maximum_output: int = 16 * 1024 * 1024) -> list[dict[str, object]]:
    """Validate BZip2 candidates without persisting decoded bytes."""

    streams: list[dict[str, object]] = []
    search_from = 0
    while True:
        offset = data.find(b"BZh", search_from)
        if offset < 0:
            return streams
        search_from = offset + 1
        decoder = bz2.BZ2Decompressor()
        try:
            decoded = decoder.decompress(data[offset:], max_length=maximum_output)
        except OSError:
            continue
        if decoder.eof:
            streams.append(
                _stream_metadata(
                    offset=offset,
                    source=data[offset:],
                    decoded=decoded,
                    unused=decoder.unused_data,
                )
            )


def _valid_xz_streams(data: bytes, maximum_output: int = 16 * 1024 * 1024) -> list[dict[str, object]]:
    """Validate XZ candidates without interpreting random signature hits as files."""

    streams: list[dict[str, object]] = []
    search_from = 0
    magic = b"\xfd7zXZ\x00"
    while True:
        offset = data.find(magic, search_from)
        if offset < 0:
            return streams
        search_from = offset + 1
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
        try:
            decoded = decoder.decompress(data[offset:], max_length=maximum_output)
        except lzma.LZMAError:
            continue
        if decoder.eof:
            streams.append(
                _stream_metadata(
                    offset=offset,
                    source=data[offset:],
                    decoded=decoded,
                    unused=decoder.unused_data,
                )
            )


def inspect_bytes(
    data: bytes,
    *,
    display_name: str = "<memory>",
    deep: bool = False,
) -> dict[str, object]:
    """Return a privacy-preserving structural inventory for ``data``.

    ``deep`` enables validation attempts for self-contained zlib streams.  It
    still performs no extraction to disk and never tries keys or transforms.
    """
    compressed = zlib.compress(data, level=9) if data else b""
    inventory: dict[str, object] = {
        "schema_version": 1,
        "display_name": display_name,
        "size": len(data),
        "sha256": sha256(data).hexdigest().upper(),
        "entropy": round(shannon_entropy(data), 6),
        "zlib_compression_ratio": round(len(compressed) / len(data), 6) if data else 0.0,
        "alignment": {"mod_16": len(data) % 16, "mod_4096": len(data) % 4096},
        "printable_ascii_string_count": _count_ascii_strings(data),
        "magic_signature_candidates": _magic_hits(data),
        "cortex_m_vector_candidate_offsets": _cortex_m_vector_candidates(data),
        "block_repetition": [_block_repeat_stats(data, size) for size in (16, 32, 256)],
        "entropy_windows": _entropy_windows(data),
        "analysis_limitations": [
            "A byte-signature candidate is not proof of an embedded file.",
            "High entropy is compatible with encryption, compression, or encoded data.",
            "No decryption, key guessing, or firmware execution was attempted.",
        ],
    }
    if deep:
        inventory["verified_zlib_streams"] = _valid_zlib_streams(data)
        inventory["verified_gzip_streams"] = _valid_gzip_streams(data)
        inventory["verified_bz2_streams"] = _valid_bz2_streams(data)
        inventory["verified_xz_streams"] = _valid_xz_streams(data)
    return inventory


def inspect_file(path: str | Path, *, deep: bool = False) -> dict[str, object]:
    """Read one local file and return its structural inventory."""
    source = Path(path)
    return inspect_bytes(source.read_bytes(), display_name=source.name, deep=deep)


def compare_files(left: str | Path, right: str | Path) -> dict[str, object]:
    """Compare opaque files without exposing their contents.

    The comparison only reports structural coincidence (such as a shared
    aligned tail block); it must not be read as evidence of an encryption mode
    or shared firmware code.
    """
    left_path = Path(left)
    right_path = Path(right)
    left_data = left_path.read_bytes()
    right_data = right_path.read_bytes()
    left_blocks = Counter(
        left_data[offset : offset + 16]
        for offset in range(0, len(left_data) - 15, 16)
    )
    right_blocks = Counter(
        right_data[offset : offset + 16]
        for offset in range(0, len(right_data) - 15, 16)
    )
    shared = set(left_blocks).intersection(right_blocks)
    left_tail = left_data[-16:] if len(left_data) >= 16 else b""
    right_tail = right_data[-16:] if len(right_data) >= 16 else b""
    return {
        "schema_version": 1,
        "left": {"name": left_path.name, "size": len(left_data), "sha256": sha256(left_data).hexdigest().upper()},
        "right": {"name": right_path.name, "size": len(right_data), "sha256": sha256(right_data).hexdigest().upper()},
        "same_bytes": left_data == right_data,
        "shared_aligned_16_byte_block_kinds": len(shared),
        "shared_aligned_16_byte_block_instances_lower_bound": sum(
            min(left_blocks[block], right_blocks[block]) for block in shared
        ),
        "same_16_byte_tail": left_tail == right_tail,
        "left_tail_sha256_16": sha256(left_tail).hexdigest()[:16].upper(),
        "right_tail_sha256_16": sha256(right_tail).hexdigest()[:16].upper(),
        "analysis_limitations": [
            "Shared 16-byte blocks alone do not identify an algorithm or a key.",
            "No plaintext recovery is implied by this structural comparison.",
        ],
    }
