# Firmware Container Analysis

Date: 2026-07-24

This was static-only inspection. No container was executed, decrypted, modified,
or sent to the device.

## VERIFIED STATICALLY

| File | Size | Shannon entropy | Plain MCU vector table |
|---|---:|---:|---|
| `ExtFlashDat.bin` | 30,629,611 | 7.9771 | absent |
| DM100 `McuCode.bin` | 287,552 | 7.9993 | absent |
| DM300 `McuCode.bin` | 259,648 | 7.9994 | absent |
| DM300 `Erase.bin` | 1,792 | 7.7094 | absent |

All four files lack a recognizable cleartext magic/header, useful version/model
strings, and a plausible STM32 vector table at offset zero. DM100 and DM300 MCU
files end with the same repeated 16-byte pattern; `Erase.bin` also has a
repeating tail block. The updater references these files by fixed relative path:

- `bin\DM100\McuCode.bin`
- `bin\DM300\McuCode.bin`
- `bin\DM300\Erase.bin` (with fallback `bin\Erase.bin`)
- `bin\ExtFlashDat.bin`

## HIGH CONFIDENCE

The near-maximum entropy and block-pattern tails are consistent with encrypted,
encoded, or compressed containers with block padding. They are not raw ARM
firmware images. Static evidence is insufficient to distinguish encryption from
a proprietary transform, and no attempt was made to defeat it.

## UNKNOWN

- container header, keying, signature, and address metadata
- MCU family beyond the USB VID/context inference
- bootloader/application separation
- external-flash layout
- whether `Erase.bin` is device-executed code or host-side opaque data

The filename `Erase.bin` is treated as dangerous regardless of format.
