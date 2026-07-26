"""Capture orchestration: raw packets -> normalized transfers -> grouped analysis."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..protocol.models import Direction, TransferType, UsbTransfer
from .pcapng import iter_packets
from .usbpcap import LINKTYPE_USBPCAP, decode_usbpcap


@dataclass
class DeviceSeen:
    bus: int
    address: int
    transfers: int

    def to_dict(self) -> dict[str, object]:
        return {"bus": self.bus, "address": self.address, "transfers": self.transfers}


@dataclass
class EndpointGroup:
    endpoint: int
    direction: Direction
    transfer_type: TransferType
    transfers: list[UsbTransfer] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"0x{self.endpoint:02X} {self.direction.value} {self.transfer_type.value}"

    def delays(self) -> list[float]:
        ts = [t.timestamp for t in self.transfers]
        return [round(b - a, 6) for a, b in zip(ts, ts[1:], strict=False)]

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoint": f"0x{self.endpoint:02X}",
            "direction": self.direction.value,
            "transfer_type": self.transfer_type.value,
            "count": len(self.transfers),
            "payload_lengths": sorted({t.length for t in self.transfers}),
        }


@dataclass
class CaptureAnalysis:
    capture_id: str
    transfers: list[UsbTransfer]
    devices: list[DeviceSeen]
    groups: list[EndpointGroup]
    linktype_counts: dict[int, int]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        from .transactions import correlate_urb_transactions

        transactions, orphans = correlate_urb_transactions(self.transfers)
        return {
            "capture_id": self.capture_id,
            "transfer_count": len(self.transfers),
            "urb_transaction_count": len(transactions),
            "incomplete_urb_transaction_count": sum(not item.complete for item in transactions),
            "orphan_urb_record_count": len(orphans),
            "live_transfer_count": len(self.live_transfers),
            "synthetic_transfer_count": len(self.synthetic_transfers),
            "devices": [d.to_dict() for d in self.devices],
            "device_address_changes": [
                {"timestamp": ts, "from": old, "to": new}
                for ts, old, new in self.device_address_changes
            ],
            "groups": [g.to_dict() for g in self.groups],
            "linktype_counts": {str(k): v for k, v in self.linktype_counts.items()},
            "warnings": self.warnings,
        }

    def repeated_payloads(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for t in self.transfers:
            counts[f"0x{t.endpoint:02X}:{t.payload_hex}"] += 1
        return {k: v for k, v in counts.items() if v > 1}

    @property
    def live_transfers(self) -> list[UsbTransfer]:
        return [t for t in self.transfers if not t.synthetic]

    @property
    def synthetic_transfers(self) -> list[UsbTransfer]:
        return [t for t in self.transfers if t.synthetic]

    @property
    def device_address_changes(self) -> list[tuple[float, int, int]]:
        changes: list[tuple[float, int, int]] = []
        previous: int | None = None
        for transfer in self.transfers:
            if previous is not None and transfer.address != previous:
                changes.append((transfer.timestamp, previous, transfer.address))
            previous = transfer.address
        return changes


def analyze(path: str | Path, *, bus: int | None = None, address: int | None = None) -> CaptureAnalysis:
    data = Path(path).read_bytes()
    return analyze_bytes(data, capture_id=Path(path).name, bus=bus, address=address)


def analyze_bytes(
    blob: bytes,
    *,
    capture_id: str = "capture",
    bus: int | None = None,
    address: int | None = None,
) -> CaptureAnalysis:
    transfers: list[UsbTransfer] = []
    linktype_counts: dict[int, int] = defaultdict(int)
    warnings: list[str] = []

    for pkt in iter_packets(blob):
        linktype_counts[pkt.linktype] += 1
        if pkt.linktype != LINKTYPE_USBPCAP:
            continue
        try:
            rec = decode_usbpcap(pkt.data)
        except ValueError as exc:
            warnings.append(f"packet {pkt.index}: {exc}")
            continue
        if bus is not None and rec.bus != bus:
            continue
        if address is not None and rec.device != address:
            continue
        transfers.append(
            UsbTransfer(
                index=pkt.index,
                timestamp=pkt.timestamp,
                endpoint=rec.endpoint,
                direction=rec.direction,
                transfer_type=rec.transfer_type,
                payload=rec.payload,
                bus=rec.bus,
                address=rec.device,
                actual_length=len(rec.payload),
                urb_function=rec.function,
                status=rec.status,
                irp_id=rec.irp_id,
                usbpcap_info=rec.info,
                synthetic=rec.is_synthetic,
                capture_id=capture_id,
            )
        )

    non_usbpcap = {k: v for k, v in linktype_counts.items() if k != LINKTYPE_USBPCAP}
    if non_usbpcap and not transfers:
        warnings.append(
            "No USBPcap (linktype 249) packets found. This capture may be a network "
            f"capture. Link types seen: {non_usbpcap}."
        )
    if transfers and not any(not t.synthetic for t in transfers):
        warnings.append(
            "All USBPcap records are synthetic descriptor injection; no live URB records found."
        )

    devices = _summarize_devices(transfers)
    groups = _group_by_endpoint(transfers)
    return CaptureAnalysis(capture_id, transfers, devices, groups, dict(linktype_counts), warnings)


def _summarize_devices(transfers: list[UsbTransfer]) -> list[DeviceSeen]:
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for t in transfers:
        counts[(t.bus, t.address)] += 1
    return [DeviceSeen(bus, addr, n) for (bus, addr), n in sorted(counts.items())]


def _group_by_endpoint(transfers: list[UsbTransfer]) -> list[EndpointGroup]:
    groups: dict[tuple[int, Direction, TransferType], EndpointGroup] = {}
    for t in transfers:
        key = (t.endpoint, t.direction, t.transfer_type)
        if key not in groups:
            groups[key] = EndpointGroup(t.endpoint, t.direction, t.transfer_type)
        groups[key].transfers.append(t)
    return [groups[k] for k in sorted(groups, key=lambda k: (k[0], k[1].value))]
