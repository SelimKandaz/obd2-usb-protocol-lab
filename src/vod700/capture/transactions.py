"""USBPcap submit/completion correlation for offline capture analysis.

USBPcap emits one record when the host submits an IRP and another when it
completes.  The payload direction differs by endpoint direction: an OUT
payload normally appears on submission, while an IN payload normally appears
on completion.  Treating both records as independent protocol messages causes
false duplicate packets and can mistake a controller-induced cancellation for
a device response.

This module only joins records that already exist in a capture.  It does not
open a USB device, replay a transfer, or infer the semantics of an unknown
command.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..protocol.models import Direction, TransferType, UsbTransfer
from ..protocol.verified import (
    BLOCK_READ,
    BulkReadObservation,
    inspect_bulk_read,
    parse_request,
    parse_response,
    reassemble_bulk_read_fragments,
)

USBD_STATUS_CANCELED = 0xC0010000


@dataclass(frozen=True)
class UrbTransaction:
    """One USBPcap IRP submission correlated with its completion, if present."""

    submit: UsbTransfer
    completion: UsbTransfer | None
    replaced_by_submit: bool = False

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.submit.bus, self.submit.address, self.submit.irp_id or 0)

    @property
    def endpoint(self) -> int:
        return self.submit.endpoint

    @property
    def direction(self) -> Direction:
        return self.submit.direction

    @property
    def transfer_type(self) -> TransferType:
        return self.submit.transfer_type

    @property
    def complete(self) -> bool:
        return self.completion is not None

    @property
    def completion_status(self) -> int | None:
        return self.completion.status if self.completion is not None else None

    @property
    def succeeded(self) -> bool:
        return self.complete and self.completion_status == 0

    @property
    def elapsed_s(self) -> float | None:
        if self.completion is None:
            return None
        return self.completion.timestamp - self.submit.timestamp

    @property
    def payload(self) -> bytes:
        """Return the data-stage bytes for the logical transfer.

        OUT bytes are submitted by the host; IN bytes arrive on completion.
        An incomplete IN transaction has no payload rather than a fabricated
        zero-length response.
        """

        if self.direction is Direction.OUT:
            return self.submit.payload
        return self.completion.payload if self.completion is not None else b""

    @property
    def cancellation_observed(self) -> bool:
        """Whether the capture records the standard cancelled USB status."""

        return self.completion_status == USBD_STATUS_CANCELED

    def to_dict(self) -> dict[str, object]:
        return {
            "submit_index": self.submit.index,
            "completion_index": self.completion.index if self.completion is not None else None,
            "bus": self.submit.bus,
            "address": self.submit.address,
            "irp_id": f"0x{(self.submit.irp_id or 0):X}",
            "endpoint": f"0x{self.endpoint:02X}",
            "direction": self.direction.value,
            "transfer_type": self.transfer_type.value,
            "complete": self.complete,
            "completion_status": (
                f"0x{self.completion_status:08X}" if self.completion_status is not None else None
            ),
            "cancellation_observed": self.cancellation_observed,
            "elapsed_s": round(self.elapsed_s, 6) if self.elapsed_s is not None else None,
            "payload_length": len(self.payload),
            "payload_hex": self.payload.hex(),
            "replaced_by_submit": self.replaced_by_submit,
        }


@dataclass(frozen=True)
class FeedbackReadTransaction:
    """A capture-correlated ``0x06`` request, acknowledgement, and bulk data.

    ``feedback`` is the updater's own filename/worker terminology.  The class
    records packet relationships and integrity only; it does *not* promote
    arbitrary-address command ``0x06`` to a safe live operation.
    """

    request: UrbTransaction
    acknowledgement: UrbTransaction | None
    bulk_fragments: tuple[UrbTransaction, ...]
    observation: BulkReadObservation | None
    note: str

    @property
    def address(self) -> int:
        return parse_request(self.request.payload).address or 0

    def to_dict(self) -> dict[str, object]:
        return {
            "request_submit_index": self.request.submit.index,
            "address": f"0x{self.address:08X}",
            "request_completion_status": (
                f"0x{self.request.completion_status:08X}"
                if self.request.completion_status is not None
                else None
            ),
            "acknowledgement_completion_index": (
                self.acknowledgement.completion.index if self.acknowledgement and self.acknowledgement.completion else None
            ),
            "bulk_completion_indices": [
                item.completion.index for item in self.bulk_fragments if item.completion is not None
            ],
            "bulk_fragment_lengths": [len(item.payload) for item in self.bulk_fragments],
            "bulk_checksum_valid": self.observation.checksum_valid if self.observation else None,
            "bulk_data_sha256": self.observation.data_sha256 if self.observation else None,
            "note": self.note,
            "safety": "BLOCKED_PENDING_EXPLICIT_LIVE_APPROVAL",
        }


def correlate_urb_transactions(transfers: list[UsbTransfer]) -> tuple[list[UrbTransaction], list[UsbTransfer]]:
    """Join live USBPcap submit/completion records using bus/address/IRP ID.

    A given IRP value can be reused after completion, so a new submission closes
    an otherwise unfinished prior incarnation instead of merging both.  Records
    without USBPcap phase metadata are returned as orphans rather than guessed.
    """

    active: dict[tuple[int, int, int], UsbTransfer] = {}
    transactions: list[UrbTransaction] = []
    orphans: list[UsbTransfer] = []

    for transfer in transfers:
        phase = transfer.urb_phase
        if phase is None or transfer.irp_id is None:
            orphans.append(transfer)
            continue
        key = (transfer.bus, transfer.address, transfer.irp_id)
        if phase == "submit":
            prior = active.pop(key, None)
            if prior is not None:
                transactions.append(UrbTransaction(prior, None, replaced_by_submit=True))
            active[key] = transfer
            continue
        if phase == "completion":
            submit = active.pop(key, None)
            if submit is None:
                orphans.append(transfer)
            elif (
                submit.endpoint != transfer.endpoint
                or submit.direction is not transfer.direction
                or submit.transfer_type is not transfer.transfer_type
            ):
                # IRP identity is the primary key, but a malformed or
                # cross-device record must not become a fabricated logical
                # transaction. Preserve the original submission so a later
                # matching completion can still close it.
                active[key] = submit
                orphans.append(transfer)
            else:
                transactions.append(UrbTransaction(submit, transfer))
            continue
        orphans.append(transfer)

    transactions.extend(UrbTransaction(submit, None) for submit in active.values())
    transactions.sort(key=lambda item: item.submit.index)
    return transactions, orphans


def correlate_feedback_reads(transfers: list[UsbTransfer]) -> list[FeedbackReadTransaction]:
    """Recover only the capture-observed ``0x06`` -> ``0x86`` -> bulk-IN shape.

    This deliberately requires the exact acknowledged response and exact
    4,096+8-byte bulk completion pair before calculating the SUM32.  A
    cancelled request remains an incomplete record and is never represented as
    a device response.
    """

    transactions, _ = correlate_urb_transactions(transfers)
    results: list[FeedbackReadTransaction] = []
    for index, request in enumerate(transactions):
        if (
            request.endpoint != 0x01
            or request.direction is not Direction.OUT
            or request.transfer_type is not TransferType.INTERRUPT
        ):
            continue
        try:
            parsed = parse_request(request.payload)
        except ValueError:
            continue
        if parsed.command != BLOCK_READ:
            continue

        if not request.succeeded:
            if request.cancellation_observed:
                note = "request completion is USBD_STATUS_CANCELED; no device acknowledgement was captured"
            elif request.completion is None:
                note = "request has no completion record; no device acknowledgement was captured"
            else:
                note = "request completed with non-zero status; no device acknowledgement was captured"
            results.append(FeedbackReadTransaction(request, None, (), None, note))
            continue

        following = transactions[index + 1 :]
        acknowledgement = following[0] if following else None
        if (
            acknowledgement is None
            or acknowledgement.endpoint != 0x81
            or acknowledgement.direction is not Direction.IN
            or acknowledgement.transfer_type is not TransferType.INTERRUPT
            or not acknowledgement.succeeded
        ):
            results.append(
                FeedbackReadTransaction(request, acknowledgement, (), None, "missing successful 0x86 acknowledgement")
            )
            continue
        try:
            response = parse_response(acknowledgement.payload)
        except ValueError:
            results.append(
                FeedbackReadTransaction(request, acknowledgement, (), None, "acknowledgement is not a known framed response")
            )
            continue
        if response.command != BLOCK_READ:
            results.append(
                FeedbackReadTransaction(request, acknowledgement, (), None, "acknowledgement command does not match 0x06")
            )
            continue

        candidates = following[1:3]
        if len(candidates) != 2 or any(
            item.endpoint != 0x82
            or item.direction is not Direction.IN
            or item.transfer_type is not TransferType.BULK
            or not item.succeeded
            for item in candidates
        ):
            results.append(
                FeedbackReadTransaction(request, acknowledgement, tuple(candidates), None, "missing complete bulk-IN fragment pair")
            )
            continue
        try:
            observation = inspect_bulk_read(reassemble_bulk_read_fragments([item.payload for item in candidates]))
        except ValueError as exc:
            results.append(FeedbackReadTransaction(request, acknowledgement, tuple(candidates), None, str(exc)))
            continue
        results.append(
            FeedbackReadTransaction(request, acknowledgement, tuple(candidates), observation, "capture-derived bulk frame"))
    return results
