"""Offline firmware/update-container inspection helpers.

This package deliberately has no device transport dependency.  It can inventory
opaque files and identify *candidates* for familiar formats, but it never sends,
decrypts by guessing, or modifies a firmware/update artifact.
"""
from __future__ import annotations

from .archive import verify_zip_archive
from .inspect import compare_files, inspect_bytes, inspect_file
from .match import BulkArtifactMatch, match_captured_bulk_to_artifact

__all__ = [
    "BulkArtifactMatch",
    "compare_files",
    "inspect_file",
    "inspect_bytes",
    "match_captured_bulk_to_artifact",
    "verify_zip_archive",
]
