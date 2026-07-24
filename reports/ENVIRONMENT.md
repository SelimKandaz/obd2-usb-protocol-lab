# Environment Report (Phase 1)

Research host inventory. Host username and machine-specific paths are redacted.

## Operating system & shells
| Item                | Value                                        | Confidence |
|---------------------|----------------------------------------------|------------|
| OS                  | Windows 11 Home, 10.0.26200 (build 26200)    | VERIFIED   |
| Architecture        | 64-bit                                        | VERIFIED   |
| PowerShell          | 5.1.26100.8894 (Desktop edition)              | VERIFIED   |
| .NET Framework      | 4.8.09221 (release 533509)                    | VERIFIED   |
| .NET SDK / runtimes | SDK 9.0.316; runtimes 3.1.32, 8.0.29, 9.0.18  | VERIFIED   |

## Toolchain present
| Tool     | Version / path (redacted)                | Notes                         |
|----------|------------------------------------------|-------------------------------|
| Python   | 3.14.3 default; also 3.13/3.12/3.11/3.9   | project venv built on 3.13    |
| pip      | present                                   |                               |
| git      | 2.53.0.windows.2                          |                               |
| Nmap     | `C:\Program Files (x86)\Nmap`             | pulled in Npcap               |
| Npcap    | `C:\Program Files\Npcap` (driver running) | **network only — not USB**    |

## Capture tooling — MISSING (blocker for Phase 4)
| Tool      | State          |
|-----------|----------------|
| Wireshark | not installed  |
| tshark    | not installed  |
| dumpcap   | not installed  |
| USBPcap   | not installed  |
| 7-Zip     | not on PATH    |

> Npcap being installed is misleading: it captures **network** interfaces only.
> USB capture requires **USBPcap** (bundled optionally with Wireshark).

## VOD700 device — PRESENT
| Item             | Value                                         |
|------------------|-----------------------------------------------|
| Status           | OK, present                                    |
| Instance ID      | `USB\VID_0483&PID_5265\AUTOPHIX_DM`           |
| Service / driver | `WINUSB` / `winusb.inf` (Microsoft 10.0.26100.8875) |
| USB address      | 9 (changes on reconnect)                       |

Full device facts: [`../docs/DEVICE_PROFILE.md`](../docs/DEVICE_PROFILE.md).

## Official updater — NOT FOUND
No ANCEL/Autophix/VOD700 updater is installed (no registry uninstall entry) and
no matching executable/installer was found under the user profile. Phases 2–3
(updater static analysis) are blocked until the updater is placed in
`private_samples/updater/`.

## Source evidence already on host (pre-existing)
Two text dumps on the host Desktop were the basis of the initial endpoint/PnP
data and have been independently re-verified live:
- an endpoint probe dump (interface/pipe listing)
- a `pnputil` device dump

Their contents are captured (redacted) in `docs/DEVICE_PROFILE.md` and
`docs/USB_ENDPOINTS.md`.
