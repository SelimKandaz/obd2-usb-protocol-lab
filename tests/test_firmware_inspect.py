from __future__ import annotations

import gzip
import zlib
from zipfile import ZipFile

import pytest

from vod700.firmware import match_captured_bulk_to_artifact, verify_zip_archive
from vod700.firmware.inspect import compare_files, inspect_bytes, inspect_file
from vod700.mock.fixtures import build_usbpcap_pcapng, make_usbpcap_record
from vod700.protocol.models import TransferType


def test_inspect_bytes_reports_structure_without_strings():
    blob = b"\x00" * 16 + b"MZ" + b"hello" + b"\x00" * 17
    result = inspect_bytes(blob, display_name="synthetic.bin")
    assert result["display_name"] == "synthetic.bin"
    assert result["size"] == len(blob)
    assert result["printable_ascii_string_count"] == 1
    assert any(hit["name"] == "MZ" for hit in result["magic_signature_candidates"])
    assert "strings" not in result


def test_deep_inspection_validates_real_zlib_stream_without_extraction():
    wrapped = b"prefix" + zlib.compress(b"synthetic payload") + b"suffix"
    result = inspect_bytes(wrapped, deep=True)
    streams = result["verified_zlib_streams"]
    assert len(streams) == 1
    assert streams[0]["offset"] == len(b"prefix")
    assert streams[0]["decoded_length"] == len(b"synthetic payload")


def test_deep_inspection_validates_gzip_and_rejects_magic_only_candidates():
    wrapped = b"prefix" + gzip.compress(b"synthetic gzip") + b"suffix\x1f\x8b\x08"
    result = inspect_bytes(wrapped, deep=True)
    streams = result["verified_gzip_streams"]
    assert len(streams) == 1
    assert streams[0]["offset"] == len(b"prefix")
    assert streams[0]["decoded_length"] == len(b"synthetic gzip")


def test_compare_files_reports_shared_tail_without_exposing_bytes(tmp_path):
    left = tmp_path / "left.bin"
    right = tmp_path / "right.bin"
    left.write_bytes(b"A" * 16 + b"T" * 16)
    right.write_bytes(b"B" * 16 + b"T" * 16)
    result = compare_files(left, right)
    assert result["same_bytes"] is False
    assert result["same_16_byte_tail"] is True
    assert result["shared_aligned_16_byte_block_kinds"] == 1
    assert result["left"]["name"] == "left.bin"
    assert inspect_file(left)["size"] == 32


def test_match_bulk_compares_only_hashes_and_equality(tmp_path):
    artifact = tmp_path / "opaque.bin"
    data = bytes(range(256)) * 16
    artifact.write_bytes(data)
    body = bytes.fromhex("55aa55aa") + data
    frame = body + (sum(body) & 0xFFFFFFFF).to_bytes(4, "big")
    capture = tmp_path / "synthetic.pcapng"
    capture.write_bytes(
        build_usbpcap_pcapng(
            [
                (
                    0,
                    make_usbpcap_record(
                        endpoint=0x02,
                        payload=frame,
                        transfer_type=TransferType.BULK,
                        irp_id=1,
                    ),
                )
            ]
        )
    )

    result = match_captured_bulk_to_artifact(capture, artifact)
    assert result.bytes_equal is True
    assert result.frame_checksum_valid is True
    assert result.data_length == 4096


def test_verify_zip_archive_matches_an_already_extracted_tree_without_extracting(tmp_path):
    archive = tmp_path / "release.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("release/bin/opaque.bin", b"opaque")
        zip_file.writestr("release/readme.txt", b"metadata")
    extracted = tmp_path / "extracted"
    (extracted / "bin").mkdir(parents=True)
    (extracted / "bin" / "opaque.bin").write_bytes(b"opaque")
    (extracted / "readme.txt").write_bytes(b"metadata")

    result = verify_zip_archive(archive, extracted)
    assert result["all_crc_valid"] is True
    assert result["stripped_top_level_directory"] == "release"
    assert result["all_members_match"] is True
    assert result["matching_member_count"] == 2


def test_verify_zip_archive_refuses_path_traversal_members(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../outside.bin", b"must not be addressed")
    extracted = tmp_path / "extracted"
    extracted.mkdir()

    with pytest.raises(ValueError, match="unsafe ZIP member path"):
        verify_zip_archive(archive, extracted)
