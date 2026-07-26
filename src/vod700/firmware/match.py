"""Offline comparison between a captured bulk-OUT frame and a local artifact.

The official updater's captured update-stage frame contains an opaque 4 KiB
data slice.  This module proves or disproves byte equality with a local,
already-owned update artifact without printing either payload.  It cannot build
or transmit an update frame.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

from ..capture import analyze
from ..protocol.models import Direction, TransferType
from ..protocol.verified import (
    BULK_BODY_SIZE,
    BULK_TRANSFER_SIZE,
    BULK_WRITE_MAGIC,
    inspect_bulk_write,
)


@dataclass(frozen=True)
class BulkArtifactMatch:
    """Privacy-preserving evidence for one captured 4 KiB update-data slice."""

    capture_name: str
    capture_transfer_index: int
    artifact_name: str
    artifact_sha256: str
    artifact_size: int
    artifact_offset: int
    data_length: int
    page_count_for_artifact: int
    frame_checksum_valid: bool
    frame_data_sha256: str
    artifact_slice_sha256: str
    bytes_equal: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _update_bulk_submits(capture: str | Path, *, bus: int | None, address: int | None):
    analysis = analyze(capture, bus=bus, address=address)
    return [
        transfer
        for transfer in analysis.transfers
        if transfer.endpoint == 0x02
        and transfer.direction is Direction.OUT
        and transfer.transfer_type is TransferType.BULK
        and transfer.urb_phase == "submit"
        and len(transfer.payload) == BULK_TRANSFER_SIZE
    ]


def match_captured_bulk_to_artifact(
    capture: str | Path,
    artifact: str | Path,
    *,
    offset: int = 0,
    bus: int | None = None,
    address: int | None = None,
    transfer_index: int | None = None,
) -> BulkArtifactMatch:
    """Compare one captured 4 KiB bulk-OUT body with a local artifact slice.

    The function refuses ambiguous captures and bounds the slice fully inside
    the supplied file.  It returns hashes and equality only, never raw update
    bytes.  This function is intentionally isolated from every WinUSB module.
    """

    if offset < 0:
        raise ValueError("artifact offset must be non-negative")
    candidates = _update_bulk_submits(capture, bus=bus, address=address)
    if transfer_index is not None:
        candidates = [item for item in candidates if item.index == transfer_index]
    if not candidates:
        raise ValueError("no 0x02 bulk-OUT submit with an observed 0x1008-byte frame was found")
    if len(candidates) != 1:
        raise ValueError("capture has multiple matching bulk-OUT submits; specify transfer_index")

    transfer = candidates[0]
    observation = inspect_bulk_write(transfer.payload)
    if observation.prefix != BULK_WRITE_MAGIC:
        raise ValueError(f"unexpected bulk-OUT magic: {observation.prefix.hex()}")
    if observation.body_length != BULK_BODY_SIZE + 4:
        raise ValueError("captured bulk-OUT body does not have magic plus exactly one 4 KiB data slice")

    artifact_path = Path(artifact)
    artifact_data = artifact_path.read_bytes()
    end = offset + BULK_BODY_SIZE
    if end > len(artifact_data):
        raise ValueError("artifact does not contain a full 4 KiB slice at the requested offset")
    artifact_slice = artifact_data[offset:end]
    frame_data = transfer.payload[4:-4]
    return BulkArtifactMatch(
        capture_name=Path(capture).name,
        capture_transfer_index=transfer.index,
        artifact_name=artifact_path.name,
        artifact_sha256=sha256(artifact_data).hexdigest().upper(),
        artifact_size=len(artifact_data),
        artifact_offset=offset,
        data_length=len(frame_data),
        page_count_for_artifact=(len(artifact_data) + BULK_BODY_SIZE - 1) // BULK_BODY_SIZE,
        frame_checksum_valid=observation.checksum_valid,
        frame_data_sha256=sha256(frame_data).hexdigest().upper(),
        artifact_slice_sha256=sha256(artifact_slice).hexdigest().upper(),
        bytes_equal=frame_data == artifact_slice,
    )
