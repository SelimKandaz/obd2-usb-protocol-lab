# Driver Package Analysis

Date: 2026-07-24

All files were read as text or metadata only. `install driver.bat` was not
executed, and the existing Microsoft WinUSB binding was not changed.

## VERIFIED STATICALLY

The batch file selects x86 or x64 and invokes `pnputil -i -a` for all three INF
families. Every INF installs Microsoft's `WinUSB.sys`, service `WinUsb`, start
type 3, through `Include=winusb.inf` / `Needs=WINUSB.NT`. It registers:

`{F70242C7-FB25-443B-9E7E-A4260F373982}`

as `DeviceInterfaceGUIDs` and uses `WdfCoInstaller01011.dll`. The INF declares
`KmdfLibraryVersion=1.9`; the coinstaller filename is from the KMDF 1.11
redistributable generation. The x86/x64 distinctions are architecture sections
and coinstaller binaries, not protocol differences.

| Family | VID/PID/REV | Driver dates | VOD700 match |
|---|---|---|---|
| DM100 | `0483:5265:0200` | 2017-01-05 | exact |
| DM100HC | `2E88:4605:0200` | 2021-10-18 | no |
| DM300 | `0483:5750:0200` | 2016-11-11 | no |

## VERIFIED LIVE + VERIFIED STATICALLY

The connected VOD700 is `0483:5265:0200`, instance label `Autophix_DM`, and is
already bound to Microsoft WinUSB. Therefore the package's DM100 device family
is the exact hardware-ID match. Static updater code independently compares the
device descriptor product ID to `0x5265` and selects the
`bin\DM100\McuCode.bin` branch.

Conclusion: VOD700 is a DM100-platform updater target with HIGH confidence.
This is a platform mapping, not a claim that every DM100 command is safe or
identical across products.

## Other text findings

- `README.txt` tells users to run the bundled driver installer as administrator;
  this lab did not do so.
- `note.txt` describes sending `Feedback.bin` to ANCEL support.
- `Update log.txt` describes diagnostic-tool software/library changes, including
  code clearing and scan/data-flow features. It does not document the USB
  protocol.
- Neither `{DEE824EF-729B-4A0E-9C14-B7117D33A817}` nor endpoint assumptions are
  present in the INF files.

