# VOD700 Protocol Lab — Milestone 8

Date: 2026-07-26

## Scope

Offline/static/capture analysis only. No device packet was sent, no updater was
executed, no firmware artifact was modified, and no vehicle was connected.

## Delivered engineering

- Added USBPcap IRP submit/completion correlation and capture-derived
  `0x06`/bulk read grouping. It preserves `USBD_STATUS_CANCELED` as a host
  containment result rather than inventing a device response.
- Added parsers for the capture-known dangerous `0x03` and `0x01` frame shapes
  and inspectors for both bulk frame layouts. No dangerous builder or dispatch
  path was added.
- Added offline `firmware match-bulk`, which checks an observed update bulk
  page against a local artifact via checksums and hashes only.
- Added offline `firmware verify-archive`, which validates ZIP CRCs and exact
  member equality against an existing extracted tree without extracting it.
- Expanded firmware inventory validation to zlib, gzip, BZip2, and XZ streams
  without extraction to disk.
- Added disabled feedback and Review & Print memory plans with explicit range,
  size, signature, and no-transport guardrails.
- Added a versioned protocol knowledge base, state machine, memory map,
  external research record, and validator integrated into project verification.
- Added ESP32-oriented portable reference material and updated safety/docs.

## New discoveries

| Discovery | Evidence | Classification |
|---|---|---|
| Feedback worker reads 32 x 4 KiB pages at `capacity-0x50000` | static + two captured pages | CAPTURE_VERIFIED + STATIC_ANALYSIS_SUPPORTED |
| Review & Print worker reads 30 x 4 KiB pages at `capacity-0x30000` and requires `AUTOPHIX` | static | STATIC_ANALYSIS_SUPPORTED |
| `0x82` logical read frame is 4-byte magic + 4 KiB data + big-endian SUM32 | static + capture | CAPTURE_VERIFIED + STATIC_ANALYSIS_SUPPORTED |
| `0x03=0x0047` counts DM100 4 KiB pages | static + capture + artifact | CAPTURE_VERIFIED + STATIC_ANALYSIS_SUPPORTED |
| captured bulk update data equals DM100 page zero | capture + static + offline match | CAPTURE_VERIFIED + STATIC_ANALYSIS_SUPPORTED + REPLAY_VERIFIED |
| MFC Update ID 1 dispatches worker `0x00410310`; Feedback ID 1005 dispatches `0x0040DB30` | static MFC command maps + callback pushes | STATIC_ANALYSIS_SUPPORTED |
| static VOD700 update path proceeds DM100 command `0x03` -> ExtFlash command `0x04` -> final interrupt command `0x02` | static control flow | STATIC_ANALYSIS_SUPPORTED |
| non-VOD `0x07 -> 0x87` gate compares payload with `1.26` before DM300/Erase routing | static control flow | STATIC_ANALYSIS_SUPPORTED; VOD700 semantics UNKNOWN |
| opaque artifacts have no validated standard streams or raw Cortex-M vectors | offline inventory | STATIC_ANALYSIS_SUPPORTED for host artifact facts |

## Deliberate non-actions

- No `0x06`, `0x01`, `0x03`, bulk OUT, erase, reset, or unknown command was
  dispatched.
- No firmware decryption/key guessing, updater modification, driver change, or
  public binary upload occurred.
- No claim was made that the VOD700 uses the same hardware as an AD410.
- The `0x0B`/`0x06` capture is not labeled as an Update-button preflight: the
  recovered static route identifies it as the Feedback worker path.

## Next blocker

The remaining high-value evidence is physical but non-destructive: a passive
capture of normal Feedback/Review behavior or non-invasive board markings.
See `docs/NEXT_CAPTURES.md`.
