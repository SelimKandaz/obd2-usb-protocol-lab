"""A deliberately disabled plan for the capture-derived feedback region."""
from __future__ import annotations

from dataclasses import dataclass

CAPTURED_CAPACITY = 0x02000000
FEEDBACK_REGION_OFFSET_FROM_END = 0x00050000
FEEDBACK_REGION_LENGTH = 0x00020000
BLOCK_SIZE = 0x1000
ADDRESS_COUNT = FEEDBACK_REGION_LENGTH // BLOCK_SIZE
REVIEW_PRINT_REGION_OFFSET_FROM_END = 0x00030000
REVIEW_PRINT_REGION_LENGTH = 0x0001E000
REVIEW_PRINT_ADDRESS_COUNT = REVIEW_PRINT_REGION_LENGTH // BLOCK_SIZE
REVIEW_PRINT_SIGNATURE = b"AUTOPHIX"


@dataclass(frozen=True)
class FeedbackRegionPlan:
    """A specification, not an executable device operation.

    The observed updater worker uses command ``0x06`` and a 4 KiB bulk-IN
    block after the 16-byte acknowledgement.  The live dispatcher intentionally
    does not expose this class and does not import this module.
    """

    capacity: int
    start_address: int
    end_address_exclusive: int
    block_size: int
    addresses: tuple[int, ...]
    command: int = 0x06
    endpoint_out: int = 0x01
    endpoint_in: int = 0x81
    bulk_endpoint_in: int = 0x82
    dispatch_enabled: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "capacity": f"0x{self.capacity:08X}",
            "start_address": f"0x{self.start_address:08X}",
            "end_address_exclusive": f"0x{self.end_address_exclusive:08X}",
            "length": self.end_address_exclusive - self.start_address,
            "block_size": self.block_size,
            "address_count": len(self.addresses),
            "first_addresses": [f"0x{address:08X}" for address in self.addresses[:3]],
            "last_address": f"0x{self.addresses[-1]:08X}",
            "command": f"0x{self.command:02X}",
            "endpoint_out": f"0x{self.endpoint_out:02X}",
            "endpoint_in": f"0x{self.endpoint_in:02X}",
            "bulk_endpoint_in": f"0x{self.bulk_endpoint_in:02X}",
            "dispatch_enabled": self.dispatch_enabled,
            "safety": "BLOCKED_PENDING_EXPLICIT_LIVE_APPROVAL",
            "evidence": [
                "Update.exe+0x0040DB30 (capacity - 0x50000, 32 x 0x1000 loop)",
                "updater_first_vendor.pcapng (first three addresses and bulk-IN framing)",
            ],
            "guardrails": [
                "No USB transport code is exposed by this plan.",
                "Only the captured capacity and bounded tail region are represented.",
                "No address wraparound or arbitrary address selection is permitted.",
            ],
        }


@dataclass(frozen=True)
class ReviewPrintRegionPlan:
    """Static-only map for the updater's separate ``Review & Print`` worker.

    The worker at ``Update.exe+0x0040EFB0`` uses the same blocked ``0x06`` /
    bulk-IN transport shape but scans a different tail range.  It accepts only
    blocks whose post-transport data begins with ``AUTOPHIX``.  Neither the
    range nor the signature promotes ``0x06`` to a live-safe command.
    """

    capacity: int
    start_address: int
    end_address_exclusive: int
    block_size: int
    addresses: tuple[int, ...]
    expected_data_signature: bytes = REVIEW_PRINT_SIGNATURE
    command: int = 0x06
    endpoint_out: int = 0x01
    endpoint_in: int = 0x81
    bulk_endpoint_in: int = 0x82
    dispatch_enabled: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "capacity": f"0x{self.capacity:08X}",
            "start_address": f"0x{self.start_address:08X}",
            "end_address_exclusive": f"0x{self.end_address_exclusive:08X}",
            "length": self.end_address_exclusive - self.start_address,
            "block_size": self.block_size,
            "address_count": len(self.addresses),
            "expected_post_transport_signature_ascii": self.expected_data_signature.decode("ascii"),
            "command": f"0x{self.command:02X}",
            "endpoint_out": f"0x{self.endpoint_out:02X}",
            "endpoint_in": f"0x{self.endpoint_in:02X}",
            "bulk_endpoint_in": f"0x{self.bulk_endpoint_in:02X}",
            "dispatch_enabled": self.dispatch_enabled,
            "safety": "BLOCKED_PENDING_EXPLICIT_LIVE_APPROVAL",
            "evidence": [
                "Update.exe+0x0040EFB0 (capacity - 0x30000, 30 x 0x1000 loop)",
                "Update.exe+0x0040F351 through +0x0040F415 (AUTOPHIX check)",
                "Update.exe+0x0040F6D0 (Review & Print.txt output path)",
            ],
            "guardrails": [
                "Static analysis only; no matching live capture is available.",
                "No USB transport code is exposed by this plan.",
                "The content and the meaning of the post-signature fields are unknown.",
            ],
        }


def feedback_region_plan(capacity: int) -> FeedbackRegionPlan:
    """Build the one bounded offline plan supported by current evidence."""
    if capacity != CAPTURED_CAPACITY:
        raise ValueError(
            "only the captured 0x02000000 capacity is supported; arbitrary capacity values are blocked"
        )
    if capacity < FEEDBACK_REGION_OFFSET_FROM_END:
        raise ValueError("capacity underflows the capture-derived feedback-region offset")
    start = capacity - FEEDBACK_REGION_OFFSET_FROM_END
    end = start + FEEDBACK_REGION_LENGTH
    if end > capacity or end < start:
        raise ValueError("feedback-region calculation overflowed or crossed reported capacity")
    addresses = tuple(range(start, end, BLOCK_SIZE))
    if len(addresses) != ADDRESS_COUNT or addresses[-1] + BLOCK_SIZE != end:
        raise ValueError("feedback-region address plan is not exactly block aligned")
    return FeedbackRegionPlan(capacity, start, end, BLOCK_SIZE, addresses)


def review_print_region_plan(capacity: int) -> ReviewPrintRegionPlan:
    """Build the second static-only, capacity-bounded storage plan."""
    if capacity != CAPTURED_CAPACITY:
        raise ValueError(
            "only the captured 0x02000000 capacity is supported; arbitrary capacity values are blocked"
        )
    if capacity < REVIEW_PRINT_REGION_OFFSET_FROM_END:
        raise ValueError("capacity underflows the review-print-region offset")
    start = capacity - REVIEW_PRINT_REGION_OFFSET_FROM_END
    end = start + REVIEW_PRINT_REGION_LENGTH
    if end > capacity or end < start:
        raise ValueError("review-print-region calculation overflowed or crossed reported capacity")
    addresses = tuple(range(start, end, BLOCK_SIZE))
    if len(addresses) != REVIEW_PRINT_ADDRESS_COUNT or addresses[-1] + BLOCK_SIZE != end:
        raise ValueError("review-print-region address plan is not exactly block aligned")
    return ReviewPrintRegionPlan(capacity, start, end, BLOCK_SIZE, addresses)
