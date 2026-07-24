from __future__ import annotations

from vod700.protocol import checksums as ck

CHECK = b"123456789"


def test_crc8_known_vectors():
    assert ck.crc8(CHECK, 0x07, 0x00, False, False, 0x00) == 0xF4  # CRC-8/SMBUS
    assert ck.CRC_8["CRC-8/MAXIM-DOW"](CHECK) == 0xA1


def test_crc16_known_vectors():
    assert ck.CRC_16["CRC-16/CCITT-FALSE"](CHECK) == 0x29B1
    assert ck.CRC_16["CRC-16/XMODEM"](CHECK) == 0x31C3
    assert ck.CRC_16["CRC-16/MODBUS"](CHECK) == 0x4B37
    assert ck.CRC_16["CRC-16/ARC"](CHECK) == 0xBB3D
    assert ck.CRC_16["CRC-16/KERMIT"](CHECK) == 0x2189


def test_simple_checksums():
    assert ck.xor8(b"\xaa\x01\x00") == 0xAB
    assert ck.sum8(b"\x01\x02\x03") == 0x06
    assert (ck.sum8(b"\x10\x20") + ck.sum8_twos_complement(b"\x10\x20")) & 0xFF == 0


def test_analyze_trailing_finds_xor8_across_frames():
    def xor_framed(body: bytes) -> bytes:
        return body + bytes([ck.xor8(body)])

    frames = [xor_framed(b) for b in (b"\xaa\x01\x00", b"\xaa\x01\x01", b"\xaa\x02\x05")]
    _all, consistent = ck.analyze_trailing(frames)
    names = {c.name for c in consistent}
    assert "XOR8" in names


def test_analyze_trailing_requires_multiple_frames():
    # A single frame must never yield a "consistent" checksum claim.
    frames = [b"\xaa\x01\x00" + bytes([ck.xor8(b"\xaa\x01\x00")])]
    _all, consistent = ck.analyze_trailing(frames, min_frames=2)
    assert consistent == []


def test_analyze_trailing_rejects_wrong_checksum():
    frames = [b"\x01\x02\x99", b"\x03\x04\x99"]  # trailing byte not a real checksum
    _all, consistent = ck.analyze_trailing(frames)
    assert all(c.name != "XOR8" for c in consistent)
