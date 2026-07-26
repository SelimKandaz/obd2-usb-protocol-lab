# Device Memory and Storage Analysis

Date: 2026-07-26

Machine-readable map: [`knowledge/memory_map.json`](../knowledge/memory_map.json).

## Result

The updater treats `0x02000000` as an addressable capacity boundary and uses
two bounded tail windows. This is strong evidence about its **host-side address
arithmetic**, not proof of a physical flash type, MCU memory map, or safe
arbitrary memory read.

The `Feedback` dialog control (ID 1005) is statically mapped to the first
worker. The Review & Print worker's UI entry remains unknown; the region table
does not imply that the two features share a user action.

| Region | Range | Size | Worker evidence | Capture evidence | Meaning | Live status |
|---|---|---:|---|---|---|---|
| Feedback tail window | `0x01FB0000..0x01FD0000` | `0x20000` | `+0x0040DB30`, 32 pages | first two pages captured | host writes `Feedback.bin` | blocked |
| Review & Print window | `0x01FD0000..0x01FEE000` | `0x1E000` | `+0x0040EFB0`, 30 pages | none | accepts `AUTOPHIX` prefix, host writes text file | blocked |
| Unmapped tail | `0x01FEE000..0x02000000` | `0x12000` | range arithmetic only | none | unknown | blocked |
| MCU internal flash | unknown | unknown | no decoded MCU image | none | unknown | blocked |
| External flash/database | unknown | unknown | `ExtFlashDat.bin` path only | none | unknown | blocked |

## Capture-correlated feedback transport

The static feedback worker sends the 16-byte `0x06` frame with a little-endian
address in bytes 3–6 and a wire selector byte `0x10` at byte 8. A successful
captured transaction is:

```text
0x01 OUT: 55 AA 06 <address LE32> 00 10 00 00 00 00 00 00 <SUM8>
0x81 IN : AA 55 86 00 00 00 00 00 00 00 00 00 00 00 00 <SUM8>
0x82 IN : AA 55 AA 55 | 4096 data bytes | SUM32BE
```

USBPcap records each observed logical bulk frame as one 4096-byte completion
followed by an 8-byte completion. The updater requests `0x1008` bytes, so the
project reassembles only that exact captured shape. Both completed pages had a
valid trailer `0x000FF1FE` and all-`FF` data.

The third request was cancelled before an interrupt acknowledgement. It is
preserved as an incomplete transaction rather than treated as an empty page or
device error response.

## Read-only determination

`0x06` is **not enabled for any live read**. Current evidence establishes a
read-shaped updater workflow, but not safe semantics for arbitrary addresses,
all firmware states, or the selector field. It is update-adjacent and the
project must not use it for probing.

The following offline-only commands are deliberately available:

```powershell
vod700 memory feedback-plan
vod700 memory review-print-plan
vod700 capture transactions private_samples\captures\updater_first_vendor.pcapng --bus 1 --address 6
```

They create no USB handle and no device traffic. A future implementation may
only add a live reader after all of these are true:

1. A passive capture demonstrates completion of a normal, non-update Feedback
   or Review & Print workflow.
2. Static/dynamic evidence independently excludes a write/erase mode for this
   command and selector.
3. The owner explicitly approves a bounded experiment limited to already
   observed addresses and transfer sizes.

## Architecture implications

- The `0x02000000` capacity must not be assumed to mean 32 MiB of MCU internal
  flash. It could be a logical address space, serial flash, or an updater
  protocol capacity.
- The tail windows are differentiated by updater behavior (`Feedback.bin` vs.
  `Review & Print.txt` and the `AUTOPHIX` signature); they are not proven
  filesystem partitions.
- No safe nonvolatile-memory dump exists today. The disabled planning module
  prevents arbitrary capacities, ranges, address wraparound, or bulk-OUT use.
