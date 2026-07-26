# Firmware and Update-Container Analysis

Date: 2026-07-26

All work in this report was offline. Original package files remain in ignored
`private_samples/`; no artifact was executed, modified, decrypted by guessing,
or transmitted by this project.

The retained original release ZIP (`38,747,673` bytes; SHA-256
`0F23628CF36C57541D51458A1871D3E4EEEDF87BB73690661414540530BBC25C`) has
27 file members and `48,960,974` total uncompressed bytes. Standard ZIP CRC
validation succeeded and all 27 members byte-match the local extracted working
tree. The reusable command is:

```powershell
vod700 firmware verify-archive private_samples\updater\original\6a448a83cddfb.zip `
  private_samples\updater `
  --out private_samples\analysis\release_archive_verification.json
```

## Artifact inventory

| Artifact | Size | SHA-256 | Entropy | Standard streams verified | Cortex-M vector candidates |
|---|---:|---|---:|---|---|
| `bin/DM100/McuCode.bin` | 287,552 | `D36A9A4ECD084CB787096089DCBB4FF71104D25BBAA07F69D60CA3B9AFEB4C78` | 7.999322 | none (`zlib`, gzip, BZip2, XZ) | none |
| `bin/DM300/McuCode.bin` | 259,648 | `5FC2749FE3E4E8294645412D82513E480BE2C5E2D6A4DD6A21ED66D52CF98F4B` | 7.999350 | none | none |
| `bin/DM300/Erase.bin` | 1,792 | `1E560520B78CAD7D12143E2FDADAA3FFFD8203AB9A3DE8BA18E67C48E6006FC6` | 7.709386 | none | none |
| `bin/ExtFlashDat.bin` | 30,629,611 | `1A2B538D499125871436383A78FD6FE0158183970473A43088DB0C2D2CFC993B` | 7.977107 | none | none |

The reproducible scanner records sizes, hashes, entropy, alignment, printable
string counts, conservative magic candidates, repeated aligned-block statistics,
window entropy, vector-table candidates, and complete standard-stream validation
results without emitting artifact bytes:

```powershell
vod700 firmware inspect private_samples\updater\bin\DM100\McuCode.bin --deep
vod700 firmware inspect private_samples\updater\bin\ExtFlashDat.bin --deep
vod700 firmware compare private_samples\updater\bin\DM100\McuCode.bin private_samples\updater\bin\DM300\McuCode.bin
```

## Container findings

### PHYSICALLY/CAPTURE/STATIC supported transport fact

The updater selects `bin\DM100\McuCode.bin` when the device descriptor PID is
`0x5265`. The capture's `0x03` field is `0x0047`, exactly
`ceil(287552 / 4096)`. The subsequent official-updater bulk OUT data page is
byte-for-byte equal to offset zero of DM100 `McuCode.bin`:

| Comparison | Result |
|---|---|
| Capture data page length | 4,096 bytes |
| Capture data SHA-256 | `D0D028CE79946A7DB54E4B0D7A424085AC15CE4273007FC9D007F5B781CA313B` |
| DM100 offset | `0x00000000` |
| DM100 page SHA-256 | same |
| Byte equality | true |
| Captured frame SUM32BE | valid |

Run the privacy-preserving proof locally:

```powershell
vod700 firmware match-bulk `
  private_samples\captures\updater_update_stage.pcapng `
  private_samples\updater\bin\DM100\McuCode.bin `
  --bus 1 --address 6
```

This is strong evidence that the observed host update worker copies opaque
DM100 source bytes into the transport frame unchanged. It rules out a
host-side decrypt/decompress transform **in this worker and for this page**.
It does not rule out a device-side transform, a different later worker, or a
custom format with no transform.

### STATIC_ANALYSIS_SUPPORTED update artifact sequence

The exact `Update` control launches worker `0x00410310`. In its VOD700 PID
success path, it calls the dangerous transfer worker with:

| Static callsite | Host artifact / input | Stage command | Wire evidence |
|---:|---|---:|---|
| `Update.exe+0x00410C25` | `bin/DM100/McuCode.bin` | `0x03` | captured for the first page only |
| `Update.exe+0x00410F10` | `bin/ExtFlashDat.bin` | `0x04` | none retained |
| `Update.exe+0x00411002` | zero-page-count finalization | `0x02` interrupt | none retained |

This is a host control-flow result, not permission to execute any stage. The
command-`0x04` and final-command-`0x02` device responses and effects
remain UNKNOWN and blocked. `ExtFlashDat.bin` must not be assumed to map to a
physical external-flash chip merely from its name.

The common worker returns early only for command `0x02`; command `0x04` follows
the same static `0x01` page-handshake and pipe-selector-3 bulk-OUT loop as the
captured `0x03` stage. No command-`0x04` packet or ExtFlash byte is retained in
the capture corpus.

### Package/driver relationship

The read-only package inventory covers the release tree, nested archive copy,
text files, driver files, and binaries. The bundled DM100 WinUSB INF maps
`USB\VID_0483&PID_5265&REV_0200` and the same interface GUID used by the
updater. The installer batch file also contains DM300 and DM100HC entries, but
it was never run and does not identify the VOD700's MCU. This supports the
DM100 family mapping already established by the updater's product-ID branch;
it does not justify driver changes.

### STATIC_ANALYSIS_SUPPORTED updater transform inventory

The PE import inventory shows WinUSB, SetupAPI, and basic file I/O. It contains
no imported CryptoAPI/BCrypt/key-derivation API and no imported standard
compression API (`zlib`, deflate/uncompress, LZMA, BZip2, Zstd, LZ4, cabinet).
This is a narrow negative result: it does not rule out custom/static-linked
code or device-side processing.

### Opaque artifact structure

- Neither `McuCode.bin` exposes a plausible clear Cortex-M vector table under
  the scanner's conservative SRAM/flash candidate test.
- DM100 and DM300 share a final aligned 16-byte block hash
  `AC91DFB38C437D1D`; 2,654 aligned 16-byte block values occur in both files.
  This demonstrates structural similarity only, not an encryption algorithm,
  key, or common executable code.
- `ExtFlashDat.bin` has repeated blocks and lower-entropy windows but no valid
  standard zlib/gzip/BZip2/XZ stream. Random `MZ`, gzip, or BZip2 magic hits
  were deliberately not treated as embedded files because their decoders did
  not reach end-of-stream.
- `Erase.bin` is opaque and remains dangerous by role/path regardless of its
  entropy or format.

## Firmware code recovery result

No executable VOD700 MCU firmware image has been recovered. Consequently, the
following remain **UNKNOWN**:

- MCU part number, architecture, endianness, vector table, and reset handler
- bootloader/application boundaries and physical flash layout
- external flash/filesystem layout
- USB dispatcher, CAN/ISO-TP/K-Line/LIN code, watchdog, and identity storage
- container header, signature, decryption, or device-side unpacking logic

The project does not call opaque high-entropy bytes “encrypted firmware” as a
fact. The supported conclusion is only: **the package artifacts are opaque,
not recovered as raw MCU executable images, and the captured DM100 page is
transported unchanged by the analyzed host worker.**

## Safe next evidence

The next safe paths are further static call-graph work or a passive capture of
a normal feedback/review workflow. Firmware writing, erase operations, and
unverified `0x06` reads remain prohibited. Board marking inspection or a
separately proven non-mutating storage export would be needed before making a
credible MCU/flash claim.
