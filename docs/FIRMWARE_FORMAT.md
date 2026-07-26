# Firmware / Update Container Format

Status: **opaque artifacts inventoried; no raw MCU firmware recovered**.

The canonical findings and hashes are in
[`reports/FIRMWARE_CONTAINER_ANALYSIS.md`](../reports/FIRMWARE_CONTAINER_ANALYSIS.md).
All private binaries remain ignored. The project never executes, modifies,
uploads, or transmits them.

## Established facts

- `Update.exe` chooses `bin\DM100\McuCode.bin` for VOD700 PID `0x5265`.
- The observed dangerous update worker transports the first DM100 4 KiB page
  unchanged inside `55AA55AA + page + SUM32BE`.
- The captured `0x03` value `0x0047` equals
  `ceil(DM100 McuCode.bin size / 4096)`.
- Static VOD700 success flow then names `ExtFlashDat.bin` for dangerous command
  `0x04` and invokes a final interrupt command `0x02`; neither later wire
  format is captured or permitted to run.
- The four packaged artifacts have no recovered standard zlib/gzip/BZip2/XZ
  stream and no plausible clear Cortex-M vector table under the conservative
  scanner.

These facts do **not** identify an encryption algorithm, key, signature,
device-side decoder, MCU model, or flash layout.

## Offline tools

```powershell
# Structural inventory; no extraction or device I/O
vod700 firmware inspect private_samples\updater\bin\DM100\McuCode.bin --deep
vod700 firmware inspect private_samples\updater\bin\ExtFlashDat.bin --deep

# Structural comparison; reports hashes/statistics, not artifact bytes
vod700 firmware compare private_samples\updater\bin\DM100\McuCode.bin `
  private_samples\updater\bin\DM300\McuCode.bin

# Match an official-updater captured bulk page to a local artifact slice.
# It only reports hashes/equality and never builds or sends a frame.
vod700 firmware match-bulk private_samples\captures\updater_update_stage.pcapng `
  private_samples\updater\bin\DM100\McuCode.bin --bus 1 --address 6

# Validate a locally retained release ZIP against an already extracted tree.
# It checks ZIP CRCs and hashes only; it does not extract or transmit anything.
vod700 firmware verify-archive private_samples\updater\original\release.zip `
  private_samples\updater
```

## Interpretation rules

- A magic-byte hit in high-entropy data is a candidate only. The scanner lists
  a standard compression stream only after the decoder reaches EOF.
- High entropy is compatible with encryption, compression, encoding, or opaque
  records; it is not a cryptographic conclusion.
- The absence of host CryptoAPI/compression imports does not rule out custom,
  statically linked, or device-side transformation.
- `Erase.bin` is dangerous by its updater role/path and is never passed to any
  client or transport code.

## Unknowns and evidence required

No code recovery or firmware-section mapping can be claimed until an actual
executable image is recovered or independently acquired as a lawful, safe
artifact. The next safe evidence is static call-graph work, passive capture of
normal storage-export workflows, or non-invasive board-marking inspection—not
an update transfer, erase action, guessed decoder, or blind protocol probe.
