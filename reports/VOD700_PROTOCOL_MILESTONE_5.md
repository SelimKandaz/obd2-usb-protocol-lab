# VOD700 Protocol Lab — Milestone 5

Date: 2026-07-25

## Status

This preparation milestone is superseded by `VOD700_PROTOCOL_MILESTONE_6.md`,
which contains the successful live first-transaction capture. The canonical
reconnect baseline was not repeated or modified.

## Completed safely

- Confirmed repository HEAD `ab9e9998d26e932ad77ff93027a6be7b1b7c72f8` before work.
- Confirmed the VOD700 is present as a WINUSB device (`VID_0483&PID_5265`).
- Added `scripts/capture_updater_first_vendor.ps1`, which dynamically selects
  the unique USBPcap WinUSB target, captures the complete root hub with
  injection disabled, waits for the official updater, requires one owner click,
  observes until the first USB record (maximum 15 seconds), then contains the
  updater.
- Confirmed the script parses successfully in Windows PowerShell.
- Reconstructed dialog resource 102 statically: Update control ID 1,
  Exit control ID 2, progress ID 1000, status ID 1001, Feedback ID 1005.
- Recorded the static-only candidate `55 AA 0B 00 00 00 00 00 00 00 00 00 00 00 00 0A`.

## Historical boundary

At the time of this preparation milestone no live vendor-specific USB transfer
had been captured. The later canonical evidence and exact hashes are recorded
in `reports/HANDSHAKE_ANALYSIS.md`; client policy remains disabled.

## Capture attempt

The first elevated attempt reached `CAPTURE_ACTIVE` and `READY`, but the
controller then timed out waiting for a separate click-signal file. The owner
interface displayed `Open File C:\\USBPcapCaptures\\bin\\McuCode.bin Fail!`.
The resulting PCAP was header-only (24 bytes), so it is not a canonical live
capture and contains no protocol evidence. The controller was changed to
require no signal file and to contain the updater automatically after the
  bounded post-click window. The updater executable is now matched by exact
  path so a different `Update.exe` copy cannot be captured accidentally.

## Safety boundary

No independent vendor request was sent. No replay, firmware operation, erase,
driver replacement, vehicle connection, or updater modification occurred.
