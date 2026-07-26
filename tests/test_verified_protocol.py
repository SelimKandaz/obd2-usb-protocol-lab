import pytest

from vod700.protocol.verified import (
    build_block_read,
    build_storage_query,
    classify_bulk_in,
    inspect_bulk_write,
    parse_observed_request,
    parse_observed_response,
    parse_request,
    parse_response,
)


def test_storage_query_matches_live_capture():
    raw = bytes.fromhex("55aa0b0000000000000000000000000a")
    assert build_storage_query() == raw
    parsed = parse_request(raw)
    assert parsed.command == 0x0B
    assert parsed.checksum == 0x0A


def test_block_read_matches_live_capture():
    raw = bytes.fromhex("55aa060000fb01001000000000000011")
    assert build_block_read(0x1FB0000) == raw
    parsed = parse_request(raw)
    assert parsed.command == 0x06
    assert parsed.address == 0x1FB0000
    assert parsed.block_length == 0x10


def test_captured_responses_and_checksums():
    storage = parse_response(bytes.fromhex("aa558b0000000200000000000000008c"))
    block = parse_response(bytes.fromhex("aa558600000000000000000000000085"))
    assert (storage.command, storage.value_u32_le, storage.checksum) == (0x0B, 0x2000000, 0x8C)
    assert (block.command, block.value_u32_le, block.checksum) == (0x06, 0, 0x85)


def test_observed_lens_preserve_unknown_command_bytes():
    request = bytes.fromhex("55aa0500000000000000000000000004")
    response = bytes.fromhex("aa550500000000000000000000000004")
    observed_request = parse_observed_request(request)
    observed_response = parse_observed_response(response)
    assert observed_request.command == 0x05
    assert observed_response.response_command == 0x05
    assert observed_response.request_command is None
    assert observed_response.raw == response


def test_invalid_frame_is_rejected():
    with pytest.raises(ValueError, match="checksum"):
        parse_request(bytes.fromhex("55aa0b00000000000000000000000000"))


def test_captured_bulk_patterns_are_classified_without_semantics():
    assert classify_bulk_in(bytes.fromhex("aa55aa55") + b"\xff" * 4092) == "4096-byte-aa55aa55-ff-fill"
    assert classify_bulk_in(bytes.fromhex("ffffffff000ff1fe")) == "8-byte-ffffffff000ff1fe-trailer"
    assert classify_bulk_in(b"other") == "unknown"


def test_bulk_write_observation_validates_captured_sum_without_builder():
    body = bytes.fromhex("55aa55aa") + bytes(range(32))
    frame = body + (sum(body) & 0xFFFFFFFF).to_bytes(4, "big")
    observed = inspect_bulk_write(frame)
    assert observed.prefix == b"\x55\xAA\x55\xAA"
    assert observed.body_length == len(body)
    assert observed.checksum_valid is True
