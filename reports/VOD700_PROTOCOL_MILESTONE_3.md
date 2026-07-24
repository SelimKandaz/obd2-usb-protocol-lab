# VOD700 Protocol — Milestone 3 Checkpoint

Date: 2026-07-24

## Outcome

All non-elevated static work is complete. The first passive capture is blocked
only on owner approval of the Windows UAC prompt needed for direct USBPcap
access. The updater was not executed and no independent vendor request was sent.

## Repository and safety

- Starting HEAD: `c9b9772`
- Branch: `main`
- Initial worktree: clean
- Safety policy: `identify` and `version` both refused dispatch
- Live read-only checks: two interfaces found; descriptor strings and all four
  endpoint descriptors matched the prior device profile
- Baseline: 41 tests passed; Ruff and mypy clean; Python compilation and wheel
  build passed

## Evidence and host security

- Original ZIP hash verified:
  `0F23628CF36C57541D51458A1871D3E4EEEDF87BB73690661414540530BBC25C`
- `Update.exe` hash verified:
  `F705FB6C6276FA52F75DD88269408D5CF061048F5EEB5451212EB1986D862C4D`
- Firmware hashes verified against the supplied values.
- ZIP: 41 entries, no traversal/absolute path, duplicate name, or nested archive.
- Inventory: 82 files, 24 unique hashes, 23 duplicate groups; evidence retained.
- Defender targeted scan: no new detections; real-time protection enabled.
- Defender exclusions: unknown because elevation is required to enumerate them.

## Updater and driver

- Native x86 Visual C++ 2013/MFC application; not .NET; unsigned.
- PE timestamp `2022-09-14T00:54:02Z`; five normal sections; no strong packer
  indicator.
- AD410 product metadata is consistent with an OEM-customized shared DM100
  updater lineage (`DM100UpdateCustom_OEM_ANCEL` internal build path).
- Driver families:
  - DM100 = `0483:5265:0200` (exact VOD700 match)
  - DM100HC = `2E88:4605:0200`
  - DM300 = `0483:5750:0200`
- Static code independently compares PID `0x5265` and selects the DM100 image.
- Interface GUID found: `{F70242C7-FB25-443B-9E7E-A4260F373982}`.
- The second live interface GUID is not embedded in the updater.

## WinUSB and protocol static findings

The updater imports SetupAPI enumeration, `CreateFileA`, WinUSB initialization,
descriptor/interface/pipe queries, pipe policy, overlapped read/write, and
cleanup. It does not import `WinUsb_ControlTransfer` or `DeviceIoControl`.

Verified request frame:

`55 AA <command> <12 command-specific bytes> <additive-sum8>`

The checksum byte is `sum(bytes[0:15]) & 0xFF`, established from function
`0x0040EC70`. Interrupt requests are exactly 16 bytes on `0x01`; responses are
exactly 16 bytes on `0x81`. Callers expect response opcode `command + 0x80`.

Static candidates:

- `0x0B`: capacity/size query candidate; response bytes 3–6 parsed LE32
- `0x06`: block-read setup candidate; request bytes 3–6 contain LE32 address,
  followed by bulk-IN
- `0x07`: family-path command, meaning unknown
- `0x03` / `0x0A`: special long-timeout commands, meanings unknown

None is classified safe from static evidence alone.

## Firmware containers

All four containers are high-entropy and lack clear headers, useful strings, or
plain STM32 vectors. Repeated tail blocks suggest opaque encoded/encrypted/
compressed block containers. No decryption or signature bypass was attempted.

## Capture checkpoint

- USBPcap driver: installed and running
- VOD700 latest address/port: 9 / port 9
- selected interface: `\\.\USBPcap1`
- dry run: passed with 18-second bound, no updater arguments
- real captures: none
- capture hashes/counts/timeline/heartbeat: unavailable

`dumpcap` does not enumerate USBPcap on this host. A direct-USBPcap fallback was
added and dry-run verified. Direct capture requires elevation. Two UAC launch
requests timed out without approval; no updater process appeared and no capture
file was created.

## Stop condition

The project has not reached a defensible active-request proposal because the
second evidence source (passive capture) is missing. No policy entry was changed.
The immediate owner action is to approve UAC for the bounded passive capture,
not to approve an active vendor request.
