# VOD700 Reverse-Engineering — Status Report

Master status for the VOD700 Protocol Lab. Host username and machine-specific
paths are redacted. Confidence tags: VERIFIED · HIGH · MEDIUM · LOW · UNKNOWN.

## 1. Repository
- Path (redacted): `…\vod700-protocol-lab`
- Layout per `README.md`; Python package under `src/vod700/`.
- `private_samples/` is local-only and git-ignored (see `docs/PRIVATE_SAMPLES.md`).

## 2. Git
- Initialized (`main`). Focused commits per the commit policy (see `git log`).

## 3. Windows & tool versions (VERIFIED)
- Windows 11 Home 10.0.26200 (64-bit); PowerShell 5.1.26100.
- .NET Framework 4.8; .NET SDK 9.0.316 (runtimes 3.1/8.0/9.0).
- Python 3.14 (also 3.13/3.12/3.11/3.9); git 2.53; Nmap + Npcap present.
- Wireshark / tshark / USBPcap / 7-Zip: **not installed**.
- Full detail: [`ENVIRONMENT.md`](ENVIRONMENT.md).

## 4. Official updater path & identity
- **NOT PRESENT** on the host. No registry uninstall entry; no matching
  installer/executable under the user profile. → Phases 2–3 blocked.

## 5. Updater technology
- **UNKNOWN** — cannot be determined until the updater binary is provided.

## 6. SHA-256 hashes
- Updater: none (absent). Firmware: none (absent).
- Tooling to produce them is ready: `scripts\hash_updater_files.ps1`.

## 7. WinUSB imports / classes found
- In the updater: **UNKNOWN** (absent).
- On the device side (VERIFIED, live): the device binds to Microsoft WinUSB via
  `MS_COMP_WINUSB`; our own read-only client uses `SetupDiGetClassDevs`,
  `WinUsb_Initialize`, `WinUsb_GetDescriptor`, `WinUsb_QueryPipe` — reads only.

## 8. VID/PID/interface references (VERIFIED, live)
- VID `0x0483` (STMicroelectronics), PID `0x5265`, REV `0x0200`, bcdUSB `2.00`.
- Strings: Manufacturer `Autophix`, Product `Automotive Diagnostic Device`,
  Serial `Autophix DM`.
- Interface 0: class/sub/proto `0xFF/0xFF/0x00`, 4 endpoints
  (`0x81` int-IN/16, `0x01` int-OUT/16, `0x82` bulk-IN/64, `0x02` bulk-OUT/64).
- Interface GUIDs: `{f70242c7-…}`, `{dee824ef-…}` (+ generic USB device GUID).

## 9. Firmware / update files discovered
- **None.** → Phase 8 blocked pending a sample in `private_samples/firmware/`.

## 10. Is USBPcap installed?
- **No.** Neither USBPcap nor Wireshark/tshark is installed. Npcap is present
  (via Nmap) but captures **network** interfaces only, not USB.

## 11. Passive capture command / procedure
- Install Wireshark **with the USBPcap component**, then follow
  [`../docs/CAPTURE_HANDSHAKE.md`](../docs/CAPTURE_HANDSHAKE.md). Target the
  current USB address (print it with `scripts\capture_prereqs.ps1`; it was `9`).
  Passive only: launch updater → let it detect → wait 10–20 s → close → stop.

## 12. Files created
- Python package (`src/vod700/**`): protocol models/checksums/framing/parser;
  native pcapng+USBPcap analyzer; read-only WinUSB client + safety policy;
  mock/replay + synthetic fixtures; CLI.
- Read-only PowerShell scripts (`scripts/**`).
- Docs (`docs/**`), reports (`reports/**`), tests (`tests/**`).

## 13. Tests run (VERIFIED this session)
- `pytest`: **41 passed**.
- `ruff check`: clean. `mypy`: clean (22 source files).
- Live read-only smoke: `vod700 devices` / `descriptors` / `endpoints` all
  succeeded against the connected device.

## 14. Current blockers
1. **USBPcap/Wireshark not installed** → no USB capture yet (Phases 4–7).
2. **Official updater absent** → no static analysis (Phases 2–3).
3. **No firmware sample** → no container analysis (Phase 8).

## 15. Exact next action required from the project owner
1. Install **Wireshark** and tick the **USBPcap** component during setup.
2. Place the official VOD700 updater into `private_samples\updater\`
   (installer or extracted folder — do **not** run an update).
3. Record the passive handshake capture per `docs/CAPTURE_HANDSHAKE.md` and save
   it to `private_samples\captures\handshake.pcapng`.

With any one of these, the corresponding analysis pipeline (already built and
tested) can run immediately. No active USB communication will occur until a
request is verified, documented, approved, and fixture-tested.
