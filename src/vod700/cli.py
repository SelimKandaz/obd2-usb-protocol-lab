"""Command-line interface for the VOD700 Protocol Lab.

Read-only by construction. The device-touching commands (`devices`,
`descriptors`, `endpoints`) issue only standard USB descriptor reads. The
`identify`, `version`, and `listen` verbs are gated and report *why* they are
refused rather than sending anything. The verified `storage-query` transaction
is opt-in and requires an explicit ``--approve-live`` flag.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from . import PRODUCT_ID, VENDOR_ID, __version__


def _dump_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _cmd_devices(args: argparse.Namespace) -> int:
    from .client import readonly_client, winusb

    if not winusb.WINUSB_AVAILABLE:
        print(f"WinUSB unavailable on this platform: {winusb._IMPORT_ERROR}", file=sys.stderr)
        return 2
    try:
        paths = readonly_client.list_device_paths()
    except winusb.WinUsbError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        _dump_json({"paths": paths})
        return 0
    if not paths:
        print("No VOD700 WinUSB interface paths found. Is the device connected?")
        return 1
    print(f"Found {len(paths)} interface path(s) for VID 0x{VENDOR_ID:04X} PID 0x{PRODUCT_ID:04X}:")
    for p in paths:
        print(f"  {p}")
    return 0


def _cmd_probe(args: argparse.Namespace, what: str) -> int:
    from .client import readonly_client, winusb

    if not winusb.WINUSB_AVAILABLE:
        print(f"WinUSB unavailable on this platform: {winusb._IMPORT_ERROR}", file=sys.stderr)
        return 2
    try:
        probe = readonly_client.probe()
    except winusb.WinUsbError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        _dump_json(probe.to_dict())
        return 0

    if not probe.paths:
        print("No device found.")
        return 1
    print(f"Opened: {probe.opened_path or '(none)'}")
    if what in ("descriptors", "all") and probe.device_descriptor:
        print("\nDevice descriptor:")
        for k, v in probe.device_descriptor.items():
            print(f"  {k:<20} {v}")
        if probe.strings:
            print("\nString descriptors:")
            for k, v in probe.strings.items():
                print(f"  {k:<20} {v!r}")
    if what in ("endpoints", "all"):
        print("\nEndpoints (WinUsb_QueryPipe):")
        if probe.pipes:
            for p in probe.pipes:
                print(
                    f"  {p['pipe_id']} {p['direction']:<3} {p['pipe_type']:<10} "
                    f"maxpkt={p['max_packet_size']} interval={p['interval']}"
                )
        else:
            print("  (none reported)")
        if probe.configuration:
            for iface in probe.configuration.get("interfaces", []):
                print(
                    f"  interface {iface['bInterfaceNumber']} "
                    f"class={iface['bInterfaceClass']}/{iface['bInterfaceSubClass']}"
                    f"/{iface['bInterfaceProtocol']}"
                )
    if probe.errors:
        print("\nNotes:")
        for e in probe.errors:
            print(f"  - {e}")
    return 0


def _cmd_gated(name: str) -> int:
    from .client import readonly_client
    from .client.policy import PolicyError

    fn = getattr(readonly_client, name)
    try:
        fn()
    except (PolicyError, readonly_client.NotVerifiedError) as exc:
        print(f"REFUSED — `{name}` is gated (this is by design):\n", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 3
    return 0  # pragma: no cover - unreachable until a command is enabled


def _cmd_storage_query(args: argparse.Namespace) -> int:
    """Run the verified 0x0B query only with an explicit CLI approval flag."""
    if not args.approve_live:
        print(
            "REFUSED — `storage-query` requires --approve-live; "
            "the default path sends no vendor bytes.",
            file=sys.stderr,
        )
        return 3

    from .client import policy, transaction, winusb
    from .client.readonly_client import list_device_paths

    if not winusb.WINUSB_AVAILABLE:
        print(f"WinUSB unavailable on this platform: {winusb._IMPORT_ERROR}", file=sys.stderr)
        return 2

    spec = policy.REGISTRY["storage_query"]
    previous_enabled = spec.enabled
    spec.enabled = True
    try:
        paths = list_device_paths()
        if not paths:
            print("No VOD700 WinUSB interface paths found.", file=sys.stderr)
            return 1
        with winusb.WinUsbDevice(paths[0]) as device:
            device.require_pipe(0x01, "INTERRUPT", 16)
            device.require_pipe(0x81, "INTERRUPT", 16)
            result = transaction.run_storage_query(transaction.WinUsbPipeTransport(device))
    except (winusb.WinUsbError, transaction.TransactionError, policy.PolicyError) as exc:
        print(f"storage-query failed: {exc}", file=sys.stderr)
        return 2
    finally:
        spec.enabled = previous_enabled

    payload = {
        "endpoint_out": "0x01",
        "endpoint_in": "0x81",
        "request_hex": result.request.hex(),
        "response_hex": result.response.raw.hex(),
        "response_command": f"0x{result.response.response_command:02X}",
        "value_u32_le": result.response.value_u32_le,
        "write_length": result.write_length,
        "elapsed_s": result.elapsed_s,
    }
    if args.json:
        _dump_json(payload)
    else:
        print("storage-query OK (verified 0x0B/0x8B exchange)")
        for key, value in payload.items():
            print(f"  {key}: {value}")
    return 0


def _cmd_policy(args: argparse.Namespace) -> int:
    from .client.policy import list_commands

    specs = [s.to_dict() for s in list_commands()]
    if args.json:
        _dump_json(specs)
        return 0
    print("Command policy (all active requests are gated until verified):\n")
    for s in specs:
        flag = "DISPATCHABLE" if s["dispatchable"] else "blocked"
        print(f"  {s['name']:<10} [{flag}] safety={s['safety']} confidence={s['confidence']}")
        print(f"    {s['description']}")
    return 0


def _cmd_capture(args: argparse.Namespace) -> int:
    from .capture import analyze as run_analyze
    from .capture.exporters import write_all

    if args.capsub == "checksums":
        return _cmd_checksums(args)

    analysis = run_analyze(args.file, bus=args.bus, address=args.address)

    if args.capsub == "summary" or args.json:
        payload = analysis.to_dict()
        if args.json:
            _dump_json(payload)
        else:
            print(f"Capture: {analysis.capture_id}")
            print(f"  transfers: {len(analysis.transfers)}")
            print(f"  devices  : {[d.to_dict() for d in analysis.devices]}")
            for g in analysis.groups:
                print(f"  group    : {g.label}  x{len(g.transfers)}")
            for w in analysis.warnings:
                print(f"  warning  : {w}")
        return 0

    written = write_all(analysis, args.out, args.prefix)
    print(f"Analyzed {len(analysis.transfers)} USB transfer(s).")
    for kind, path in written.items():
        print(f"  {kind:<9} -> {path}")
    for w in analysis.warnings:
        print(f"  warning: {w}")
    return 0


def _cmd_checksums(args: argparse.Namespace) -> int:
    from .capture import analyze as run_analyze
    from .protocol.checksums import analyze_trailing

    analysis = run_analyze(args.file, bus=args.bus, address=args.address)
    target = int(args.endpoint, 0)
    frames = [t.payload for t in analysis.transfers if t.endpoint == target and t.payload]
    if len(frames) < 2:
        print(f"Need >=2 frames on endpoint 0x{target:02X}; found {len(frames)}.")
        return 1
    all_c, consistent = analyze_trailing(frames)
    print(f"Tested {len(frames)} frame(s) on 0x{target:02X} (checksum hypothesis: last byte).")
    if consistent:
        print("Consistent trailing-checksum candidates (match ALL frames):")
        for c in consistent:
            print(f"  {c.name} ({c.width_bits}-bit {c.endian}) {c.matches}/{c.total}")
    else:
        print("No trailing checksum reproduced every frame. (Try other positions/widths.)")
    return 0


def _cmd_obd2_decode(args: argparse.Namespace) -> int:
    """Decode captured CAN/ISO-TP frames; never opens a transport."""
    from .obd2 import (
        IsoTpReassembler,
        decode_dtc_response,
        decode_mode01_response,
        decode_vin_response,
        parse_can_line,
    )

    try:
        frames = [parse_can_line(line) for line in args.frames]
        reassembler = IsoTpReassembler()
        payloads = [payload for frame in frames if (payload := reassembler.feed(frame)) is not None]
    except ValueError as exc:
        print(f"OBD2 decode failed: {exc}", file=sys.stderr)
        return 2
    if not payloads:
        print("OBD2 decode incomplete: no complete ISO-TP payload", file=sys.stderr)
        return 1

    decoded: list[dict[str, object]] = []
    try:
        for payload in payloads:
            if payload.startswith(b"\x41"):
                value = decode_mode01_response(payload)
                decoded.append({"kind": "mode01", **asdict(value)})
            elif payload.startswith(b"\x43"):
                decoded.append(
                    {
                        "kind": "dtc",
                        "codes": [d.code for d in decode_dtc_response(payload)],
                        "raw": payload.hex(),
                    }
                )
            elif payload.startswith(b"I\x02"):
                decoded.append({"kind": "vin", "value": decode_vin_response(payload), "raw": payload.hex()})
            else:
                decoded.append({"kind": "raw", "payload_hex": payload.hex()})
    except ValueError as exc:
        print(f"OBD2 payload decode failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        _dump_json({"frames": [f.to_socketcan() for f in frames], "messages": decoded})
    else:
        for message in decoded:
            print(message)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vod700", description="VOD700 read-only USB protocol lab")
    p.add_argument("--version", action="version", version=f"vod700 {__version__}")
    p.add_argument("--json", action="store_true", help="machine-readable output where supported")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("devices", help="enumerate VOD700 WinUSB interface paths")
    sub.add_parser("descriptors", help="read device/config/string descriptors (read-only)")
    sub.add_parser("endpoints", help="show the endpoint map from the live device")
    sub.add_parser("identify", help="(gated) request device identity")
    sub.add_parser("version", help="(gated) request firmware/app version")
    sub.add_parser("listen", help="(gated) read the interrupt IN endpoint")
    sq = sub.add_parser("storage-query", help="verified 0x0B query (requires --approve-live)")
    sq.add_argument(
        "--approve-live",
        action="store_true",
        help="explicitly authorize one verified read-only vendor transaction",
    )
    sub.add_parser("policy", help="show the command safety policy")

    cap = sub.add_parser("capture", help="analyze a pcapng/pcap USB capture")
    caps = cap.add_subparsers(dest="capsub", required=True)
    for name in ("analyze", "summary"):
        sp = caps.add_parser(name)
        sp.add_argument("file")
        sp.add_argument("--bus", type=int, default=None)
        sp.add_argument("--address", type=int, default=None)
        if name == "analyze":
            sp.add_argument("--out", default="reports")
            sp.add_argument("--prefix", default="handshake")
    cs = caps.add_parser("checksums")
    cs.add_argument("file")
    cs.add_argument("--endpoint", default="0x01")
    cs.add_argument("--bus", type=int, default=None)
    cs.add_argument("--address", type=int, default=None)

    obd2 = sub.add_parser("obd2", help="decode captured OBD-II CAN/ISO-TP frames offline")
    obd2_sub = obd2.add_subparsers(dest="obd2sub", required=True)
    obd2_decode = obd2_sub.add_parser("decode", help="decode quoted ID#DATA CAN frames")
    obd2_decode.add_argument("frames", nargs="+", help="SocketCAN-style ID#DATA frames")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "devices":
        return _cmd_devices(args)
    if args.command == "descriptors":
        return _cmd_probe(args, "descriptors")
    if args.command == "endpoints":
        return _cmd_probe(args, "endpoints")
    if args.command in ("identify", "version", "listen"):
        return _cmd_gated(args.command)
    if args.command == "storage-query":
        return _cmd_storage_query(args)
    if args.command == "policy":
        return _cmd_policy(args)
    if args.command == "capture":
        return _cmd_capture(args)
    if args.command == "obd2" and args.obd2sub == "decode":
        return _cmd_obd2_decode(args)
    return 1
