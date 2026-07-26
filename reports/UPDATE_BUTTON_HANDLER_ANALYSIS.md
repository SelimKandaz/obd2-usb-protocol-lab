# Update and Feedback Handler Analysis

Date: 2026-07-26

## Status: static UI-to-worker edges recovered

This report is based on offline analysis of the private `Update.exe` only. No
updater process was started, patched, or driven while producing these results.
The handler names below are analyst labels, not vendor symbols.

## Dialog resource

PE resource dialog 102 is titled `Device upgrades` and contains:

| Control | ID | Class | Caption |
|---|---:|---|---|
| Update button | 1 | button (ATOM 128) | `Update` |
| Exit button | 2 | button (ATOM 128) | `Exit` |
| Progress bar | 1000 | `msctls_progress32` | — |
| Welcome/status text | 1001 | static | `Welcome to ANCEL's vehicle diagnostic tool !` |
| Feedback | 1005 | static | `Feedback` |

## Exact MFC command-map findings

The reusable private scanner (`tools/analyze_updater.py`) structurally recovers
x86 MFC `WM_COMMAND` map records. Two records belong to the application dialog
range and have notification code zero:

| Record | Control | Handler | Callback submitted to worker launcher | Classification |
|---|---:|---:|---:|---|
| `Update.exe+0x008CBA68` | 1 (`Update`) | `0x0040CFB0` | `0x00410310` | STATIC_ANALYSIS_SUPPORTED |
| `Update.exe+0x008CBA80` | 1005 (`Feedback`) | `0x0040D000` | `0x0040DB30` | STATIC_ANALYSIS_SUPPORTED |

Both handlers pass their dialog instance and callback address to the same
MFC worker-thread-launcher candidate at `0x00439380`. This is an exact code
relationship: `0x0040CFDF` pushes `0x00410310` before the call, and
`0x0040D02F` pushes `0x0040DB30` before the corresponding call. The precise
vendor/MFC symbol name of `0x00439380` remains unneeded and is not claimed.

## Recovered Update route

The `Update` control therefore launches worker `0x00410310`. That worker:

1. opens/enumerates the WinUSB device and reads its standard product ID;
2. selects `bin\DM100\McuCode.bin` when `idProduct == 0x5265`;
3. calls the dangerous transfer worker `0x00411330` with stage command `0x03`;
4. after success, formats the `ExtFlashDat.bin` path and calls the same
   worker with stage command `0x04`; and
5. calls the worker once more with final interrupt command `0x02`.

The calls are at `Update.exe+0x00410C25`, `+0x00410F10`, and `+0x00411002`.
Only the command-`0x03` transfer has retained USBPcap evidence. Command `0x04`
and final interrupt command `0x02` are **dangerous, unobserved stages**;
their device effects and responses remain UNKNOWN and blocked from replay.

The command-`0x03` capture's page count is `0x0047`, which equals the
71 pages of the private DM100 artifact. Its first bulk payload exactly matches
DM100 offset zero, as documented in
[`UPDATER_STATE_MACHINE.md`](UPDATER_STATE_MACHINE.md).

## Recovered Feedback route

The separate `Feedback` control launches `0x0040DB30`. That worker is the
independent static source of the observed read-shaped sequence:

```text
0x0B / 0x8B capacity -> 32 × (0x06 / 0x86 -> 0x82 logical 0x1008-byte read)
```

It computes `capacity - 0x50000`, copies the 4096-byte post-transport portion
of each validated bulk response into a host `Feedback.bin`, and never uses the
dangerous bulk-OUT update endpoint in this path. Its live read-only semantics
are still not independently established, so `0x06` remains blocked.

## Corrected capture attribution

The canonical first-vendor capture matches the **Feedback worker's** exact
static protocol path. It must not be described as byte-level proof that the
`Update` control itself sends `0x0B` or `0x06`: the recovered `Update` handler
instead enters the dangerous update-worker route. The controller recorded an
owner-approved updater interaction, but it did not record the precise UI
control that initiated the captured read-shaped traffic. This correction
removes an earlier unsupported UI attribution while preserving the verified
capture bytes and worker relationships.

`0x0B` remains the only independently physical-validated opt-in query. Every
`0x06` path and every update stage remains disabled in the client.
