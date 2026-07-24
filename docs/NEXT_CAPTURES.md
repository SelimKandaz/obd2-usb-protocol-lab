# Next Captures — Differential Matrix

Each capture is passive (no update-related buttons). Comparing them isolates
which packets belong to which behavior. Save every file under
`private_samples/captures/` and analyze with `vod700 capture analyze`.

| ID | Scenario                                             | Isolates                        |
|----|------------------------------------------------------|---------------------------------|
| A  | Device plugged in, updater **not** opened            | pure OS enumeration baseline    |
| B  | Updater opened, device already connected             | updater's detection handshake   |
| C  | Updater opened first, then device connected          | connect-time init ordering      |
| D  | Updater left open ~30 s, idle                        | heartbeat / periodic polling    |
| E  | Device disconnected while updater open               | disconnect handling             |
| F  | Reconnect after disconnect                           | re-init vs. cold init           |
| G  | Navigate updater UI (no update started)              | UI-triggered queries            |
| H  | Open device-info / version screen (clearly non-destructive) | identity/version request |

## How to compare
1. Run `vod700 capture analyze` on each; keep the JSONL outputs.
2. Diff endpoint groups A vs. B → the **new** interrupt OUT frames in B are the
   updater's detection/init commands.
3. In D, `repeated_payloads` surfaces heartbeat candidates (identical frames
   repeating on a fixed cadence). Confirm cadence from timestamps.
4. In H, the first OUT frame after opening the info screen is the strongest
   **device-info request** candidate; its following IN frame is the response.
5. Only after a request/response pair is stable across ≥2 captures **and**
   corroborated by updater static analysis may it be considered for the gated
   read-only client (see `READ_ONLY_CLIENT.md`).

## Do not (yet)
- Do not capture a firmware transfer.
- Do not press Update/Upgrade/Recover/Download/Flash/Firmware.
- Do not replay any captured frame back to the device.
