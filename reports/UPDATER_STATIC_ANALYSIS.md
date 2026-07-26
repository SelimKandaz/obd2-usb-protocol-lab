# Updater Static Analysis

Date: 2026-07-24

Analyzed artifact SHA-256:
`F705FB6C6276FA52F75DD88269408D5CF061048F5EEB5451212EB1986D862C4D`

This report was completed before the first execution of `Update.exe`. The
static conclusions were later correlated with the canonical passive capture and
one physical `0x0B` validation; see `VOD700_PROTOCOL_MILESTONE_7.md`.

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
| `0x07` | non-`0x5265` gate; response `0x87` payload is compared with ASCII `1.26` before the DM300 route | `55 AA 07`, remaining data zero, SUM8 `0x06` | HIGH for static bytes/path, LOW for meaning |
| `0x03` | dangerous page-count preparation | captured `55 AA 03 00 47 ... 49` | HIGH for captured layout |
| `0x04` | static ExtFlashDat preparation stage | `55 AA 04 1D 36`, remaining data zero, SUM8 `0x56` | HIGH static, no wire capture |
| `0x02` | static final interrupt stage after command `0x04` succeeds | `55 AA 02`, remaining data zero, SUM8 `0x01` | HIGH static, no wire capture |
| `0x0A` | only special 120-second timeout established | bytes unknown | LOW |

The response helper requires a 16-byte read. Callers compare response byte 2 to
request byte 2 plus `0x80` (for example, `0x0B` → `0x8B`). For command `0x0B`,
bytes 3–6 are decoded little-endian. The helper itself does not validate a
response checksum, so response-checksum behavior remains UNKNOWN.

## Dangerous and read-only candidates

The updater contains explicit firmware paths, an erase container, large bulk-OUT
frames, and update UI/state strings. Bulk-OUT logic at `0x00411330` constructs
`0x1008`-byte blocks and appends a 32-bit additive total in big-endian byte
order before pipe-selector-3 writes. These paths are dangerous and must never be
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

No command is promoted in the safety policy from static evidence alone. The
current policy promotes only the `0x0B` storage query as an explicit opt-in
after the independent physical validation documented in the later milestone.

## 2026-07-26 addendum — bounded workers and exact update frames

The present source of truth for the recovered flow is
`reports/UPDATER_STATE_MACHINE.md` and
`knowledge/updater_state_machine.json`. This addendum corrects two earlier
limitations in this report.

- `0x03` and `0x01` are no longer only timeout candidates. The separate
  official-updater capture shows exact `0x03 -> 0x83` and `0x01 -> 0x81`
  frames, while `Update.exe+0x00411330` supplies the independent construction
  path. Both are **dangerous update states**, not client commands.
- `0x06` is not merely “update-adjacent.” `+0x0040DB30` is a bounded Feedback
  export worker: `capacity - 0x50000`, 32 pages, `0x1008` bulk-IN reads, and a
  host `Feedback.bin` output. It remains blocked because this does not prove
  arbitrary-address non-mutating semantics.
- A second worker at `+0x0040EFB0` starts at `capacity - 0x30000`, reads 30
  pages through the same shape, tests `AUTOPHIX` in post-transport data, and
  makes `Review & Print.txt`. It has no live capture yet.
- The static update worker copies a 4 KiB source page directly into the
  observed `55AA55AA + page + SUM32BE` frame. Offline matching proves the
  captured page equals DM100 `McuCode.bin` offset zero; see
  `reports/FIRMWARE_CONTAINER_ANALYSIS.md`.
- All retained captured 16-byte responses satisfy SUM8. The updater helper's
  own lack of a static response-checksum check is a host-validation detail, not
  evidence against the observed wire checksum.
- Structural MFC command-map recovery resolves `Update` control ID 1 at
  `+0x008CBA68 -> 0x0040CFB0 -> callback 0x00410310` and `Feedback` control
  ID 1005 at `+0x008CBA80 -> 0x0040D000 -> callback 0x0040DB30`. The two
  handlers use the same worker-launcher candidate at `0x00439380`. Thus the
  captured `0x0B`/`0x06` sequence belongs to the Feedback worker; it is not
  static proof that the Update button itself performs that query.
- The Update worker's success path is statically ordered: VOD700 DM100 command
  `0x03` at `+0x00410C25`, then `ExtFlashDat.bin` command `0x04` at
  `+0x00410F10`, then final interrupt command `0x02` at `+0x00411002`. The
  latter two wire transactions are not captured and remain dangerous/UNKNOWN.
- The refreshed import inventory contains no imported CryptoAPI/BCrypt/key or
  standard compression API. This does not rule out custom, statically linked,
  or device-side transformation.
- The non-VOD branch at `+0x00410566` constructs a zero-payload `0x07` frame,
  expects `0x87`, and compares response bytes after the header with ASCII
  `1.26`. A match selects `DM300\McuCode.bin`; a non-match tries
  `DM300\Erase.bin` and then `bin\Erase.bin` before a dangerous worker call.
  This is a separate family path, has no VOD700 capture, and is not a version
  command candidate for the active client.

The refreshed reproducible static report is intentionally private because it
contains vendor strings:

```powershell
.\.venv\Scripts\python.exe tools\analyze_updater.py `
  --input private_samples\updater\Update.exe `
  --out private_samples\analysis\updater_static_v4.json
```
