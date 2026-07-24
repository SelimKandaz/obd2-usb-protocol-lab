# Firmware Container Analysis (Phase 8)

**Status: BLOCKED — no firmware/update sample present.**

Analysis is **static only**; a firmware file is never sent to the device, and no
encryption/signature is ever attacked. See `docs/FIRMWARE_FORMAT.md` for the
method. Place samples in `private_samples/firmware/`.

## Report skeleton (offsets/lengths/entropy only — no proprietary bytes)
| Aspect                    | Finding | Confidence |
|---------------------------|---------|------------|
| Container magic / header  | _tbd_   | UNKNOWN    |
| Format version            | _tbd_   | UNKNOWN    |
| Target device identifiers | _tbd_   | UNKNOWN    |
| Region / language         | _tbd_   | UNKNOWN    |
| Section table             | _tbd_   | UNKNOWN    |
| Compression indicators    | _tbd_   | UNKNOWN    |
| Encryption indicators     | _tbd_   | UNKNOWN    |
| Checksums / signatures    | _tbd_   | UNKNOWN    |
| Firmware version string   | _tbd_   | UNKNOWN    |
| Bootloader / app split    | _tbd_   | UNKNOWN    |

## Reminder
Do not publish or commit proprietary firmware contents. Record only derived
metadata (hashes, offsets, lengths, entropy, high-level structure).
