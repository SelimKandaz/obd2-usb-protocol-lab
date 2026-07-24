# Capture Tooling Report (Phase 1)

Date: 2026-07-24. Host username/paths redacted.

## Installed this session
| Tool     | Version   | Source                                   | Path                                   |
|----------|-----------|------------------------------------------|----------------------------------------|
| Wireshark| 4.6.7     | winget `WiresharkFoundation.Wireshark`   | `C:\Program Files\Wireshark\Wireshark.exe` |
| tshark   | 4.6.7     | (bundled with Wireshark)                 | `C:\Program Files\Wireshark\tshark.exe`|
| dumpcap  | 4.6.7     | (bundled with Wireshark)                 | `C:\Program Files\Wireshark\dumpcap.exe`|

Install command used (silent, official publisher "The Wireshark Foundation"):
```
winget install --id WiresharkFoundation.Wireshark -e --silent --accept-package-agreements --accept-source-agreements
```
The WinUSB driver on the VOD700 was **not** touched. Npcap (already present from
Nmap) was left as-is.

## USBPcap — NOT installed (blocks USB capture)
- `USBPcapCMD.exe` absent (`C:\Program Files\USBPcap\` does not exist).
- `dumpcap -D` lists **only network interfaces** (Npcap adapters: Ethernet/Wi-Fi/
  loopback/Tailscale/WSL). **No `USBPcap` interface is present.** (Interface GUIDs
  intentionally omitted from this committed report.)
- winget's *silent* Wireshark install does **not** include the optional USBPcap
  component, so it must be installed separately.

### To enable USB capture (owner action — UAC + reboot)
USBPcap installs a kernel-mode capture driver that only activates after a reboot,
so this requires the owner:
1. Install USBPcap from an official source — either the **Wireshark installer's
   USBPcap component**, or the standalone official installer at
   `https://desowin.org/usbpcap/` (USBPcap is the project the Wireshark component
   ships; it is the required USB driver, not an "unrelated" packet driver).
2. Approve the **UAC** prompt.
3. **Reboot** (the driver loads at boot).
4. Verify: `dumpcap -D` should then list one or more `USBPcap` interfaces, and
   `scripts\capture_updater_handshake.ps1 -DryRun` should report "ready".

## Verification of the orchestrator
`scripts\capture_updater_handshake.ps1 -DryRun` currently:
- detects the VOD700 (address 9), and
- **safely refuses** with install instructions because USBPcap is absent.

This is the intended gate: no capture is attempted until USBPcap is present.
