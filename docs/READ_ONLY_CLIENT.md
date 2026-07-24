# Read-Only WinUSB Client

An independent client that talks to the VOD700 through the **existing Microsoft
WinUSB driver** (no Zadig, no driver replacement). It is read-only by
construction.

## What it does today (safe, standard USB requests)

| Command                | Action                                              | Safety     |
|------------------------|-----------------------------------------------------|------------|
| `vod700 devices`       | enumerate VOD700 WinUSB interface paths (SetupAPI)   | read-only  |
| `vod700 descriptors`   | GET_DESCRIPTOR device/config/string reads            | read-only  |
| `vod700 endpoints`     | `WinUsb_QueryPipe` endpoint map                      | read-only  |
| `vod700 policy`        | show the command safety policy                        | local only |
| `vod700 capture ...`   | analyze a pcapng/pcap (offline, no device)           | local only |

These issue only **standard** USB requests (the same ones enumeration already
performs) or touch no device at all. There is intentionally **no**
`WinUsb_WritePipe` or `WinUsb_ReadPipe` binding in `client/winusb.py`.

## What is gated (refused until verified)

| Command            | Why it is refused                                             |
|--------------------|--------------------------------------------------------------|
| `vod700 identify`  | No verified request bytes exist yet (see `policy.py`).       |
| `vod700 version`   | No verified request bytes exist yet.                          |
| `vod700 listen`    | Reading the interrupt IN endpoint needs an approved ReadPipe. |

Running any of these prints the exact blocking reasons and exits non-zero. This
is the safety gate working, not a bug.

## Promoting a command from gated → enabled
A command in `src/vod700/client/policy.py` becomes dispatchable only when it is
`enabled`, classified `READ_ONLY`, at confidence ≥ HIGH, and carries **both** a
capture reference and a static-analysis reference. To enable one you must:

1. Capture the updater issuing it (passive capture).
2. Confirm the request/response bytes in the analyzer across multiple captures.
3. Cross-check the byte construction in the updater's static analysis.
4. Set `enabled=True` with the evidence references filled in.
5. Test it against a fixture / the mock device before ever touching hardware.

## Implementation notes
- Enumeration uses `SetupDiGetClassDevs` on the vendor interface GUIDs, with the
  x64 `cbSize` quirk handled (8-byte header, device path read at offset 4).
- Descriptors are parsed by `client/descriptors.py` (pure functions, unit-tested).
- The module imports cleanly on non-Windows (`WINUSB_AVAILABLE == False`); the
  CLI reports that instead of crashing, so parsers/tests run anywhere.
