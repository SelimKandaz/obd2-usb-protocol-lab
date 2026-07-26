# Protocol Findings and Remaining Hypotheses

Date: 2026-07-26

This report separates evidence classes. The machine-readable version is
`knowledge/protocol_knowledge.json`.

## Physically verified

- A connected `VID 0x0483 / PID 0x5265` VOD700 accepts the exact 16-byte
  `0x0B` request on interrupt OUT `0x01`.
- The device returns the exact 16-byte `0x8B` response on interrupt IN `0x81`.
- The response value bytes 3–6 decode little-endian as `0x02000000`.
- The exchange completes within the bounded 1,000 ms client timeout.

## Capture verified

- The canonical updater capture contains 22 genuine USBPcap URBs at bus 1,
  address 6 and no synthetic records.
- The updater sends four 16-byte interrupt OUT frames (`0x0B` then three
  `0x06` frames) and receives three completed interrupt responses.
- The three observed `0x06` addresses are `0x01FB0000`, `0x01FB1000`, and
  `0x01FB2000`; byte 8 is `0x10`.
- Each observed 16-byte interrupt frame uses `55 AA`/`AA 55` framing and the
  trailing additive SUM8 formula.
- The capture contains repeated 4,096-byte and 8-byte bulk-IN patterns.
- A separate official-updater trace contains one 4,104-byte bulk OUT beginning
  `55 AA 55 AA` with a big-endian additive SUM32 trailer. This path is
  dangerous and is not implemented.

## Static-analysis conclusions

- `Update.exe` uses WinUSB pipe selectors dynamically; selector 1 maps to
  `0x01` and selector 0 maps to `0x81` in the verified endpoint order.
- `Update.exe+0x0040E670` constructs the exact `0x0B` request and
  `0x00410010` performs the 16-byte OUT/IN exchange.
- `Update.exe+0x0040EC70` computes the request SUM8.
- The updater's selected interface GUID is
  `{F70242C7-FB25-443B-9E7E-A4260F373982}`.

## Hypotheses and unknowns

- The `0x0B` value is a capacity/size query; byte-level evidence is strong,
  but complete device-state semantics remain MEDIUM.
- `0x06` is an addressed read candidate followed by bulk-IN data; its live
  dispatch safety is UNKNOWN and the policy blocks it.
- The earlier isolated `0x05` response is an unclassified state/status
  response. It is not labeled NACK, success, or a new command.
- Bulk-IN payload semantics, heartbeat cadence, version/identify commands, and
  the full update state machine remain UNKNOWN.
- The VOD700 USB vendor protocol has not been proven to be a CAN/OBD-II bridge;
  the OBD-II module therefore remains transport-neutral and offline-only.

## Explicit non-claims

No firmware, erase, bulk-write, ECU, DTC-clear, vehicle, or guessed command
operation is implemented or inferred from these findings.
