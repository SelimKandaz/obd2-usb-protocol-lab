# VOD700 Reverse-Engineering — Current Project Status

Date: 2026-07-25

This is the current status of the independent, evidence-driven VOD700 USB
client. Historical milestone reports retain the earlier snapshots; this file
is the present acceptance record.

## Device and transport

- VID/PID: `0x0483/0x5265`, revision `0x0200`
- Microsoft WinUSB (`winusb.inf`), no driver replacement
- One vendor-specific interface (`0xFF/0xFF/0x00`)
- Interrupt OUT/IN: `0x01`/`0x81`, 16-byte packets
- Bulk OUT/IN: `0x02`/`0x82`, 64-byte packets
- Two Windows interface paths resolve to the same endpoint map
- Live descriptor/device/endpoint checks pass with the connected VOD700

## Evidence chain

Canonical reconnect baseline:

- `private_samples/captures/baseline_reconnect.pcapng`
- 20 live endpoint-0 records, address transition `5 -> 6`
- SHA-256: `3484911891084476D74E8D3553D15F13BE5676E09EED241388E7E5AEC4182878`

Canonical updater preliminary transaction:

- `private_samples/captures/updater_first_vendor.pcapng`
- 9,748 bytes; 22 live URBs; bus 1/address 6
- SHA-256: `5475B9B6C40413BB97C791C15CF286503626AEC64D90BD831CA3B1D278A8B731`
- First request: `55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A`
- Response: `AA 55 8B 00 00 00 02 00 00 00 00 00 00 00 00 8C`
- Subsequent observed read-only-shaped frames: three `0x06`/`0x86` pairs and
  preliminary bulk-IN patterns

Separate updater update-stage capture:

- `private_samples/captures/updater_update_stage.pcapng`
- One official-updater `0x02` bulk OUT (4,104 bytes) was observed
- The payload is not reproduced, implemented, or sent by this project

## Physical validation

The exact `0x0B` request was sent through the policy-gated WinUSB adapter under
explicit owner approval. The physical VOD700 returned the canonical `0x8B`
response and value `0x02000000` (33,554,432). A prior isolated attempt returned
an unclassified `0x05`; it was not retried blindly and its semantics remain
unknown. The successful validation is documented in
`reports/LIVE_STORAGE_QUERY_VALIDATION.md`.

## Implemented software

- Native PCAPNG and USBPcap record decoding, submit/completion correlation,
  address filtering, endpoint timelines, and checksum analysis
- Evidence-backed 16-byte framing, additive SUM8 parsing/building, `0x0B` and
  `0x06` offline lenses, and captured bulk-pattern inspection
- Mock/replay transport and targeted fixture tests
- WinUSB descriptor/probe client using the existing Microsoft driver
- Overlapped WinUSB pipe adapter with a policy gate
- Explicit `vod700 storage-query --approve-live` command for exactly one
  verified `0x0B`/`0x8B` transaction; default policy remains disabled
- Offline OBD-II CAN/ISO-TP codecs with SAE J1979 PID, DTC, and VIN decoders
- Wheel packaging and reproducible Windows/PowerShell workflows

## Deliberately not implemented

- `0x06` dispatch: adjacent to bulk reads/update state; bytes are parsed only
  offline
- Any `0x02` bulk OUT, firmware, erase, flash, recover, or update operation
- Guessed identify/version commands: no distinct evidence-backed bytes exist
- Live ECU/OBD2 diagnostic commands, DTC clearing, vehicle connection, or ECU
  writes

These are not missing coding tasks that can be completed honestly from the
current evidence. Implementing them would require unknown protocol bytes or
would violate the project's read-only safety boundary.

## Validation and artifact

- `pytest`: 61 passed
- Ruff: clean
- mypy: clean (28 source files)
- Python compilation: clean
- Wheel build: successful (`dist/vod700-0.1.0-py3-none-any.whl`)
- Worktree: clean
- Final validation commit: use `git rev-parse HEAD` (the worktree is clean)

The project is complete for the verified, read-only USB scope. The unknown
update/ECU protocol surface is explicitly blocked rather than fabricated.
