"""Export a :class:`CaptureAnalysis` to JSONL, CSV, and a Markdown timeline."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .analyze import CaptureAnalysis


def to_jsonl(analysis: CaptureAnalysis, path: str | Path) -> Path:
    out = Path(path)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for t in analysis.transfers:
            fh.write(json.dumps(t.to_dict(), separators=(",", ":")) + "\n")
    return out


def to_csv(analysis: CaptureAnalysis, path: str | Path) -> Path:
    out = Path(path)
    cols = [
        "index", "timestamp", "bus", "address", "endpoint_hex", "direction",
        "transfer_type", "length", "urb_function", "status", "payload_hex",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for t in analysis.transfers:
            writer.writerow(t.to_dict())
    return out


def to_markdown(analysis: CaptureAnalysis, path: str | Path, *, max_rows: int = 400) -> Path:
    out = Path(path)
    lines: list[str] = []
    lines.append(f"# Capture timeline — `{analysis.capture_id}`")
    lines.append("")
    lines.append(f"- Total transfers (USBPcap): **{len(analysis.transfers)}**")
    lines.append(f"- Link types seen: `{analysis.linktype_counts}`")
    lines.append("")

    lines.append("## Devices observed")
    lines.append("")
    lines.append("| Bus | Address | Transfers |")
    lines.append("|----:|--------:|----------:|")
    for d in analysis.devices:
        lines.append(f"| {d.bus} | {d.address} | {d.transfers} |")
    lines.append("")

    lines.append("## Endpoint groups")
    lines.append("")
    lines.append("| Endpoint | Dir | Type | Count | Payload lengths |")
    lines.append("|----------|-----|------|------:|-----------------|")
    for g in analysis.groups:
        lengths = ", ".join(str(x) for x in sorted({t.length for t in g.transfers}))
        lines.append(
            f"| 0x{g.endpoint:02X} | {g.direction.value} | {g.transfer_type.value} "
            f"| {len(g.transfers)} | {lengths} |"
        )
    lines.append("")

    repeated = analysis.repeated_payloads()
    if repeated:
        lines.append("## Repeated payloads (heartbeat / polling candidates)")
        lines.append("")
        lines.append("| Endpoint:payload | Count |")
        lines.append("|------------------|------:|")
        for key, count in sorted(repeated.items(), key=lambda kv: -kv[1])[:40]:
            lines.append(f"| `{key}` | {count} |")
        lines.append("")

    if analysis.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in analysis.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## Packet timeline")
    lines.append("")
    lines.append("| # | t (s) | Δt | EP | Dir | Type | Len | Payload (hex) |")
    lines.append("|--:|------:|---:|----|-----|------|----:|---------------|")
    t0 = analysis.transfers[0].timestamp if analysis.transfers else 0.0
    prev = t0
    for t in analysis.transfers[:max_rows]:
        rel = t.timestamp - t0
        dt = t.timestamp - prev
        prev = t.timestamp
        payload = t.payload_hex if len(t.payload_hex) <= 96 else t.payload_hex[:96] + "…"
        lines.append(
            f"| {t.index} | {rel:.4f} | {dt:.4f} | 0x{t.endpoint:02X} | {t.direction.value} "
            f"| {t.transfer_type.value[:4]} | {t.length} | `{payload}` |"
        )
    if len(analysis.transfers) > max_rows:
        lines.append("")
        lines.append(f"*(timeline truncated to {max_rows} of {len(analysis.transfers)} transfers)*")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_all(analysis: CaptureAnalysis, out_dir: str | Path, prefix: str = "handshake") -> dict[str, Path]:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return {
        "jsonl": to_jsonl(analysis, directory / f"{prefix}_packets.jsonl"),
        "csv": to_csv(analysis, directory / f"{prefix}_packets.csv"),
        "markdown": to_markdown(analysis, directory / f"{prefix}_timeline.md"),
    }
