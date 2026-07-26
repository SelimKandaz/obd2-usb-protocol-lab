# VOD700 Reverse-Engineering Status

Date: 2026-07-26

This is the current evidence boundary, not a claim that the full VOD700 or
vehicle protocol has been reconstructed.

## Completed, evidence-backed work

- Physical USB profile: WinUSB, VID/PID `0x0483/0x5265`, interface and four
  endpoint roles are physically verified.
- USBPcap tooling now correlates submit/completion pairs, including reused IRP
  values and cancellation status, without treating captures as a flat packet
  list.
- The 16-byte interrupt framing and SUM8 checksum are capture/static verified.
- `0x0B -> 0x8B` is capture/static/physical verified and remains a one-shot,
  explicit opt-in only.
- `0x06 -> 0x86 -> 0x82` has a capture-verified read-shaped layout and two
  statically mapped tail-storage workers, but is still blocked live.
- `0x03`, `0x01`, and bulk `0x02` are exact dangerous update-stage frames,
  captured from the official updater and parser-only in this project.
- The exact MFC `Update` and `Feedback` command-map records, their worker
  callbacks, and the separation between their update versus tail-read paths
  are statically recovered.
- The updater's VOD700 PID branch selects DM100 `McuCode.bin`; the first
  captured update bulk page exactly matches the first local DM100 artifact
  page, proving raw host-page transport for that frame.
- Static success control flow is DM100 command `0x03` -> `ExtFlashDat.bin`
  command `0x04` -> final interrupt command `0x02`; only command `0x03` has
  capture-verified wire bytes.
- All updater/firmware artifacts have reproducible, privacy-preserving
  inventories; the retained release ZIP passed CRC verification and all 27
  file members byte-match the local extracted tree. No raw MCU firmware
  executable or container decoder is recovered.
- The public knowledge base now includes protocol, state machine, memory map,
  external-source correlation, and validation tooling for future ESP32 work.

## Verified storage/address facts

| Item | Evidence | Confidence | Safety |
|---|---|---|---|
| Capacity boundary `0x02000000` | physical `0x0B`, capture, static decode | VERIFIED | query opt-in |
| Feedback window `0x01FB0000..0x01FD0000` | static 32-page worker + first two capture pages | HIGH | blocked |
| Review & Print window `0x01FD0000..0x01FEE000` | static 30-page `AUTOPHIX` worker | HIGH | blocked |
| Physical backing/flash type | no board/firmware proof | UNKNOWN | no claim |

## Remaining unknowns

- Exact VOD700 MCU/flash chip, board topology, bootloader and application map.
- Opaque `McuCode.bin`/`ExtFlashDat.bin` format, signature, and any device-side
  transform.
- Review & Print UI map, later update-stage wire bytes, normal post-bulk
  response, and the device effects of selectors 4 and 2.
- Meaning of the static-only non-VOD `0x07`, `0x0A`, prior unretained `0x05`,
  VOD700 version/identity commands, status/error conventions, retries, and
  reset behavior.
- Semantic guarantee that `0x06` cannot change state for all addresses/states.
- All vehicle/ECU/OBD protocol behavior; vehicle connection is out of scope.

## Current blockers

No further truthful offline extraction is available from the opaque artifacts
with the available evidence: standard stream validation, vector scanning,
static import/call analysis, artifact matching, and public correlation have
been exhausted without a raw firmware decoder or VOD700 board identity.

Further progress requires one of:

1. Passive capture of a normal Feedback or Review & Print workflow with no
   update action.
2. Non-invasive inspection of board component markings.
3. A lawfully acquired, independently identifiable firmware image or format
   specification.
4. Later, an explicitly approved and independently proven bounded read-only
   storage experiment.

No destructive, update, erase, unknown, or vehicle operation is justified by
the current evidence.
