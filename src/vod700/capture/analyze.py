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
        return {
            "capture_id": self.capture_id,
            "transfer_count": len(self.transfers),
            "devices": [d.to_dict() for d in self.devices],
            "groups": [g.to_dict() for g in self.groups],
            "linktype_counts": {str(k): v for k, v in self.linktype_counts.items()},
            "warnings": self.warnings,
        }

    def repeated_payloads(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for t in self.transfers:
            counts[f"0x{t.endpoint:02X}:{t.payload_hex}"] += 1
        return {k: v for k, v in counts.items() if v > 1}


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
                capture_id=capture_id,
            )
        )

    non_usbpcap = {k: v for k, v in linktype_counts.items() if k != LINKTYPE_USBPCAP}
    if non_usbpcap and not transfers:
        warnings.append(
            "No USBPcap (linktype 249) packets found. This capture may be a network "
            f"capture. Link types seen: {non_usbpcap}."
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
