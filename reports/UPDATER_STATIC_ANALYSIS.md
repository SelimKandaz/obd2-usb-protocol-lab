# Updater Static Analysis

Date: 2026-07-24

Analyzed artifact SHA-256:
`F705FB6C6276FA52F75DD88269408D5CF061048F5EEB5451212EB1986D862C4D`

This report was completed before the first execution of `Update.exe`.

## VERIFIED STATICALLY — PE and technology

- Native PE32 x86 GUI application; not .NET (CLR directory size 0).
- Five sections: `.text`, `.rdata`, `.data`, `.rsrc`, `.reloc`.
- PE timestamp: `2022-09-14T00:54:02Z`.
- Linker version 12.0, Visual Studio 12/MFC source paths, and static MFC/ATL
  strings identify Visual C++ 2013 with MFC.
- Entry-point RVA: `0x43E240`; image base: `0x00400000`.
- No exports.
- No Authenticode certificate/security directory; signature status `NotSigned`.
- Manifest requests `asInvoker`, `uiAccess=false`.
- No convincing packer indicator. `.text` entropy is 6.221; `.rsrc` entropy
  7.594 is explained by a large set of embedded PNG/style resources.
- Product metadata: `AD410 Update Tool`, file version `1.2.0.1`,
  company/copyright strings containing Autophix.
- Internal build paths contain
  `DM100UpdateCustom_OEM_ANCEL`, explaining the AD410/VOD700 naming mismatch as
  an OEM-customized shared DM100 updater lineage. This is not evidence of
  malware.

## VERIFIED STATICALLY — identity and device selection

- SetupAPI uses binary GUID
  `{F70242C7-FB25-443B-9E7E-A4260F373982}` at VA `0x00934AEC`.
- `{DEE824EF-729B-4A0E-9C14-B7117D33A817}` is not embedded.
- Device enumeration/open path:
  - `SetupDiGetClassDevsA` call `0x0040A2E4`
  - `SetupDiEnumDeviceInterfaces` call `0x0040A32D`
  - `SetupDiGetDeviceInterfaceDetailA` calls `0x0040A379`, `0x0040A3D7`
  - `CreateFileA` call `0x0040A212`
  - `WinUsb_Initialize` call `0x0040A23D`
  - cleanup uses `WinUsb_Free` and `CloseHandle`
- Function `0x00409740` reads the standard 18-byte device descriptor and returns
  `idProduct`.
- Caller `0x0041046D` compares that value with `0x5265`; the matching branch
  selects `bin\DM100\McuCode.bin`. This independently confirms the driver-package
  DM100 mapping.

## VERIFIED STATICALLY — WinUSB paths

Imported and used:

- `WinUsb_Initialize`, `WinUsb_Free`
- `WinUsb_GetDescriptor`
- `WinUsb_QueryInterfaceSettings`, `WinUsb_QueryPipe`
- `WinUsb_SetPipePolicy`
- `WinUsb_ReadPipe`, `WinUsb_WritePipe`
- `WinUsb_GetOverlappedResult`

Not imported: `WinUsb_ControlTransfer` and `DeviceIoControl`.

The read wrapper starts at `0x004097F0`; the write wrapper starts at
`0x00409AB0`. Both enumerate four pipes dynamically rather than embedding USB
endpoint addresses. Pipe indices resolve against the verified descriptor order:

| Updater pipe selector | Endpoint | Operation |
|---:|---|---|
| 0 | `0x81` interrupt IN | read |
| 1 | `0x01` interrupt OUT | write |
| 2 | `0x82` bulk IN | read |
| 3 | `0x02` bulk OUT | write |

The wrappers set pipe policy type 3 with a caller-provided DWORD timeout and use
overlapped I/O. The interrupt transaction helper at `0x00410010` writes exactly
16 bytes through selector 1, then reads exactly 16 bytes through selector 0.
Timeout is normally 1,000 ms, command `0x03` uses 20,000 ms, and command `0x0A`
uses 120,000 ms.

## VERIFIED STATICALLY — interrupt frame and checksum

Request checksum/builder function `0x0040EC70`:

1. writes byte 0 = `0x55`
2. writes byte 1 = `0xAA`
3. sums bytes 0 through 14 modulo 256
4. writes the result to byte 15

Therefore the trailing algorithm is an 8-bit additive checksum, not CRC-8:

`frame[15] = sum(frame[0:15]) & 0xFF`

Observed static templates:

| Command byte | Static role evidence | Request layout | Confidence |
|---:|---|---|---|
| `0x0B` | response bytes 3–6 are parsed little-endian as a size/capacity used to choose address ranges | `55 AA 0B`, remaining data zero, additive checksum | HIGH for layout, MEDIUM for meaning |
| `0x06` | address in bytes 3–6 little-endian; byte 7 zero; byte 8 `0x10`; followed by bulk-IN reads | `55 AA 06 <addrLE32> 00 10 ... <sum8>` | HIGH for layout, MEDIUM for read-block meaning |
| `0x07` | used in the non-`0x5265` device-family path before file selection/update logic | partial template only | MEDIUM for presence, LOW for meaning |
| `0x03` | only special 20-second timeout established | bytes unknown | LOW |
| `0x0A` | only special 120-second timeout established | bytes unknown | LOW |

The response helper requires a 16-byte read. Callers compare response byte 2 to
request byte 2 plus `0x80` (for example, `0x0B` → `0x8B`). For command `0x0B`,
bytes 3–6 are decoded little-endian. The helper itself does not validate a
response checksum, so response-checksum behavior remains UNKNOWN.

## Dangerous and read-only candidates

The updater contains explicit firmware paths, an erase container, large bulk-OUT
frames, and update UI/state strings. Bulk-OUT logic at `0x00411330` constructs
`0x1008`-byte blocks and appends a 32-bit additive total in big-endian byte
order before selector-3 writes. These paths are dangerous and must never be
invoked independently.

Commands `0x0B` and `0x06` look read-oriented because the first yields a size and
the second is followed by bulk-IN. This is not sufficient to classify either as
safe. They remain blocked pending passive capture correlation.

## UNKNOWN / blockers

- symbolic command names and complete state-machine semantics
- response checksum and status/NACK encoding
- heartbeat/polling behavior
- exact role of commands `0x03`, `0x06`, `0x07`, `0x0A`, `0x0B`
- device-information/version request bytes
- protocol behavior on the live VOD700

No command is promoted in the safety policy from static evidence alone.
