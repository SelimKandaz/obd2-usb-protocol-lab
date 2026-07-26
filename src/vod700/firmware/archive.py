"""Read-only ZIP package verification for updater-release provenance.

This module validates archive CRCs and compares each archive member with an
already extracted local tree.  It never extracts files, writes files, opens a
device, or submits a firmware/update packet.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

MAX_UNCOMPRESSED_ARCHIVE_BYTES = 512 * 1024 * 1024


def _member_parts(name: str) -> tuple[str, ...]:
    """Return a safe POSIX member path or reject traversal/absolute paths."""

    path = PurePosixPath(name)
    parts = path.parts
    if "\\" in name or path.is_absolute() or not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe ZIP member path: {name!r}")
    return parts


def verify_zip_archive(
    archive: str | Path,
    extracted_root: str | Path,
    *,
    maximum_uncompressed_bytes: int = MAX_UNCOMPRESSED_ARCHIVE_BYTES,
) -> dict[str, object]:
    """Verify ZIP CRCs and compare safe members to an extracted tree.

    A release ZIP often has one top-level directory while the working updater
    directory contains its contents directly.  When every member has the same
    top-level component, this function strips that component for the comparison
    only.  Hashes and equality flags are reported; member contents are not.
    """

    archive_path = Path(archive)
    root = Path(extracted_root)
    if not archive_path.is_file():
        raise ValueError(f"archive is not a file: {archive_path}")
    if not root.is_dir():
        raise ValueError(f"extracted root is not a directory: {root}")
    if maximum_uncompressed_bytes <= 0:
        raise ValueError("maximum_uncompressed_bytes must be positive")

    try:
        with ZipFile(archive_path) as zip_file:
            members = [info for info in zip_file.infolist() if not info.is_dir()]
            parts_by_member = {info.filename: _member_parts(info.filename) for info in members}
            total_uncompressed = sum(info.file_size for info in members)
            if total_uncompressed > maximum_uncompressed_bytes:
                raise ValueError(
                    f"archive uncompressed size {total_uncompressed} exceeds safety limit "
                    f"{maximum_uncompressed_bytes}"
                )
            corrupt_member = zip_file.testzip()
            top_levels = {parts[0] for parts in parts_by_member.values() if len(parts) > 1}
            strip_top_level = next(iter(top_levels)) if len(top_levels) == 1 else None

            verified_members: list[dict[str, object]] = []
            for info in members:
                parts = parts_by_member[info.filename]
                relative_parts = parts[1:] if strip_top_level and parts[0] == strip_top_level else parts
                destination = root.joinpath(*relative_parts)
                archive_bytes = zip_file.read(info)
                archive_hash = sha256(archive_bytes).hexdigest().upper()
                disk_bytes = destination.read_bytes() if destination.is_file() else None
                verified_members.append(
                    {
                        "archive_member": info.filename,
                        "relative_destination": str(Path(*relative_parts)),
                        "size": info.file_size,
                        "crc32": f"{info.CRC:08X}",
                        "archive_sha256": archive_hash,
                        "destination_present": disk_bytes is not None,
                        "destination_sha256": sha256(disk_bytes).hexdigest().upper() if disk_bytes is not None else None,
                        "bytes_equal": disk_bytes == archive_bytes if disk_bytes is not None else False,
                    }
                )
    except BadZipFile as exc:
        raise ValueError(f"invalid ZIP archive: {archive_path}") from exc

    return {
        "schema_version": 1,
        "archive_name": archive_path.name,
        "archive_size": archive_path.stat().st_size,
        "archive_sha256": sha256(archive_path.read_bytes()).hexdigest().upper(),
        "member_count": len(verified_members),
        "total_uncompressed_bytes": total_uncompressed,
        "crc_validation_member": corrupt_member,
        "all_crc_valid": corrupt_member is None,
        "stripped_top_level_directory": strip_top_level,
        "matching_member_count": sum(1 for item in verified_members if item["bytes_equal"] is True),
        "all_members_match": all(item["bytes_equal"] for item in verified_members),
        "members": verified_members,
        "analysis_limitations": [
            "ZIP CRC and byte equality verify package provenance, not firmware semantics.",
            "The function does not extract, execute, modify, or transmit archive members.",
        ],
    }
