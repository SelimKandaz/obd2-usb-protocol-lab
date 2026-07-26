"""Create a private, reproducible static summary of a native updater PE.

This helper uses ``pefile`` and ``capstone`` from the local analysis virtual
environment.  It does not execute, patch, upload, or unpack the target binary.
Its JSON output is intended for ``private_samples/analysis/`` and is therefore
not suitable for committing when it contains vendor-specific strings.

Example (from the repository root)::

    .\\.venv\\Scripts\\python.exe tools\\analyze_updater.py \
        --input private_samples\\updater\\Update.exe \
        --out private_samples\\analysis\\updater_static_v4.json
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import defaultdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

try:
    import pefile
    from capstone import CS_ARCH_X86, CS_MODE_32, Cs
except ImportError as exc:  # pragma: no cover - local analysis environment guard
    raise SystemExit(
        "This offline helper needs pefile and capstone in the analysis environment. "
        "Use the project .venv; no dependency is added to the runtime package."
    ) from exc


KNOWN_TARGETS = {
    0x0040CFB0: "mfc_update_button_handler",
    0x0040D000: "mfc_feedback_control_handler",
    0x00409740: "read_device_descriptor_product_id",
    0x004097F0: "winusb_read_wrapper",
    0x00409AB0: "winusb_write_wrapper",
    0x0040DB30: "feedback_region_worker",
    0x0040E670: "capacity_query_and_fallback_probe",
    0x0040EC70: "interrupt_sum8_builder",
    0x0040EFB0: "review_print_region_worker",
    0x00410010: "interrupt_transaction_helper",
    0x00410100: "checked_interrupt_transaction_helper",
    0x00410310: "update_worker_thread_entry",
    0x00410400: "update_worker_dispatch",
    0x00411330: "dangerous_bulk_update_worker",
    0x00439380: "mfc_worker_thread_launcher_candidate",
}

INTERESTING_IMPORTS = {
    "CreateFileA",
    "CreateFileW",
    "GetCurrentDirectoryA",
    "ReadFile",
    "WriteFile",
    "WinUsb_GetDescriptor",
    "WinUsb_GetOverlappedResult",
    "WinUsb_Initialize",
    "WinUsb_QueryPipe",
    "WinUsb_ReadPipe",
    "WinUsb_SetPipePolicy",
    "WinUsb_WritePipe",
    "SetupDiGetClassDevsA",
    "SetupDiDestroyDeviceInfoList",
    "SetupDiEnumDeviceInterfaces",
    "SetupDiGetDeviceInterfaceDetailA",
}

STRING_TERMS = (
    "McuCode",
    "Erase",
    "ExtFlash",
    "Feedback",
    "note.txt",
    "WinUsb",
    "SetupDi",
    "AD410",
    "DM100",
    "ANCEL",
)

_CRYPTO_TOKENS = ("bcrypt", "crypt", "ncrypt", "cipher")
# Do not match generic GUI helpers such as ``InflateRect``; this is an import
# inventory, not a loose string search for the word "inflate".
_COMPRESSION_TOKENS = ("zlib", "deflate", "uncompress", "lzma", "bzip", "zstd", "lz4", "cabinet")


def _entropy(data: bytes) -> float:
    from math import log2

    if not data:
        return 0.0
    counts = [data.count(bytes((value,))) for value in range(256)]
    size = len(data)
    return -sum((count / size) * log2(count / size) for count in counts if count)


def _ascii_strings(data: bytes, minimum_length: int = 4) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    pattern = re.compile(rb"[\x20-\x7e]{%d,}" % minimum_length)
    for match in pattern.finditer(data):
        out.append((match.start(), match.group().decode("ascii", "replace")))
    return out


def _section_for_offset(pe: pefile.PE, offset: int) -> tuple[str, int | None]:
    base = pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        start = section.PointerToRawData
        end = start + section.SizeOfRawData
        if start <= offset < end:
            name = section.Name.rstrip(b"\0").decode("ascii", "replace")
            return name, base + section.VirtualAddress + offset - start
    return "<file>", None


def _mfc_command_entries(pe: pefile.PE) -> list[dict[str, object]]:
    """Recover conservative x86 MFC WM_COMMAND map-shaped records.

    MFC command maps commonly encode six 32-bit fields: message, notification
    code, first control ID, last control ID, signature, and handler pointer.
    This is intentionally a structural finding rather than a claim about a
    vendor symbol.  Keeping the records in the private JSON makes the UI to
    worker relationship reproducible without executing the updater.
    """

    base = pe.OPTIONAL_HEADER.ImageBase
    text_ranges = [
        (base + section.VirtualAddress, base + section.VirtualAddress + max(section.Misc_VirtualSize, section.SizeOfRawData))
        for section in pe.sections
        if section.Name.rstrip(b"\0") == b".text"
    ]

    def in_text(value: int) -> bool:
        return any(start <= value < end for start, end in text_ranges)

    entries: list[dict[str, object]] = []
    for section in pe.sections:
        name = section.Name.rstrip(b"\0").decode("ascii", "replace")
        if name not in {".rdata", ".data"}:
            continue
        raw = section.get_data()
        for offset in range(0, len(raw) - 23, 4):
            message, code, first_id, last_id, signature, handler = struct.unpack_from("<6I", raw, offset)
            if message != 0x0111 or first_id > last_id or not in_text(handler):
                continue
            entries.append(
                {
                    "record_address": f"0x{base + section.VirtualAddress + offset:08X}",
                    "section": name,
                    "message": "WM_COMMAND",
                    "notification_code": code,
                    "first_control_id": first_id,
                    "last_control_id": last_id,
                    "mfc_signature": f"0x{signature:08X}",
                    "handler": f"0x{handler:08X}",
                    "handler_label": KNOWN_TARGETS.get(handler),
                }
            )
    return entries


def analyze(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    pe = pefile.PE(str(path), fast_load=False)
    base = pe.OPTIONAL_HEADER.ImageBase
    imports: dict[int, str] = {}
    import_groups: dict[str, list[str]] = defaultdict(list)
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        dll = entry.dll.decode("ascii", "replace")
        for item in entry.imports:
            name = item.name.decode("ascii", "replace") if item.name else f"ordinal:{item.ordinal}"
            import_groups[dll].append(name)
            imports[item.address] = f"{dll}!{name}"

    disassembler = Cs(CS_ARCH_X86, CS_MODE_32)
    disassembler.skipdata = True
    direct_calls: list[dict[str, object]] = []
    iat_calls: list[dict[str, object]] = []
    for section in pe.sections:
        if not section.Name.rstrip(b"\0").startswith(b".text"):
            continue
        for instruction in disassembler.disasm(section.get_data(), base + section.VirtualAddress):
            if instruction.mnemonic != "call":
                continue
            if instruction.op_str.startswith("0x"):
                try:
                    target = int(instruction.op_str, 16)
                except ValueError:
                    continue
                if target in KNOWN_TARGETS:
                    direct_calls.append(
                        {
                            "callsite": f"0x{instruction.address:08X}",
                            "target": f"0x{target:08X}",
                            "target_label": KNOWN_TARGETS[target],
                        }
                    )
            elif instruction.op_str.startswith("dword ptr [0x"):
                try:
                    iat = int(instruction.op_str.split("0x", 1)[1].rstrip("]"), 16)
                except ValueError:
                    continue
                imported = imports.get(iat)
                if imported and imported.rsplit("!", 1)[-1] in INTERESTING_IMPORTS:
                    iat_calls.append({"callsite": f"0x{instruction.address:08X}", "import": imported})

    strings = _ascii_strings(data)
    selected_strings = [
        {"file_offset": offset, "value": value}
        for offset, value in strings
        if any(term.lower() in value.lower() for term in STRING_TERMS)
    ]
    relevant_imports = {
        dll: sorted(name for name in names if name in INTERESTING_IMPORTS)
        for dll, names in sorted(import_groups.items())
        if any(name in INTERESTING_IMPORTS for name in names)
    }
    all_imports = sorted(name for names in import_groups.values() for name in names)
    crypto_imports = [name for name in all_imports if any(token in name.lower() for token in _CRYPTO_TOKENS)]
    compression_imports = [
        name for name in all_imports if any(token in name.lower() for token in _COMPRESSION_TOKENS)
    ]
    mfc_command_entries = _mfc_command_entries(pe)
    update_button_candidates = [
        entry
        for entry in mfc_command_entries
        if entry["notification_code"] == 0
        and entry["first_control_id"] <= 1 <= entry["last_control_id"]
    ]
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(UTC).isoformat(),
        "input": {"name": path.name, "size": len(data), "sha256": sha256(data).hexdigest().upper()},
        "pe": {
            "machine": f"0x{pe.FILE_HEADER.Machine:04X}",
            "image_base": f"0x{base:08X}",
            "entry_point": f"0x{base + pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}",
            "sections": [
                {
                    "name": section.Name.rstrip(b"\0").decode("ascii", "replace"),
                    "virtual_address": f"0x{base + section.VirtualAddress:08X}",
                    "raw_size": section.SizeOfRawData,
                    "entropy": round(_entropy(section.get_data()), 6),
                }
                for section in pe.sections
            ],
        },
        "relevant_imports": relevant_imports,
        "transform_api_inventory": {
            "crypto_or_key_api_imports": crypto_imports,
            "compression_api_imports": compression_imports,
            "interpretation": (
                "An empty list rules out only imported API usage; it does not rule out custom code, "
                "statically linked code, or device-side transformation."
            ),
        },
        "known_function_direct_calls": direct_calls,
        "interesting_iat_calls": iat_calls,
        "mfc_command_entries": mfc_command_entries,
        "update_button_candidates": update_button_candidates,
        "targeted_ascii_strings": selected_strings,
        "analysis_notes": [
            "This report is static only; no updater code was executed.",
            "Known function labels are analyst names, not vendor symbols.",
            "Call references are direct x86 calls only; virtual/indirect calls remain outside this map.",
            "MFC command entries are structural candidates; only the exact WM_COMMAND/control-ID match is asserted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"input is not a file: {args.input}", file=sys.stderr)
        return 2
    result = analyze(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote private static analysis: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
