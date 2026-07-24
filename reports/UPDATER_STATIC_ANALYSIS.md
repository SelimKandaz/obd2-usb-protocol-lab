# Updater Static Analysis (Phases 2–3)

**Status: BLOCKED — the official updater is not present on the research host.**

No ANCEL/Autophix/VOD700 updater is installed (no registry uninstall entry) and
no matching installer/executable was found under the user profile. This report
is a structured placeholder; fill it in once the updater is placed in
`private_samples/updater/`.

## Inputs required
- Official updater installer or extracted install directory → `private_samples/updater/`

## Procedure (read-only; nothing executed or patched)
1. Inventory + hashes: `scripts\hash_updater_files.ps1 -Path private_samples\updater -OutJson private_samples\updater_inventory.json`
2. Determine technology (native C/C++, .NET, Electron, Qt, Delphi, PyInstaller, Java).
3. For **.NET**: decompile with ILSpy/dnSpyEx → find the WinUSB wrapper, command
   constants, packet builders, checksum/CRC functions, firmware parser.
4. For **native**: inspect imports/strings; in Ghidra trace buffer construction
   around `WinUsb_WritePipe` / `WinUsb_ReadPipe`; identify endpoint selection,
   timeouts, retry logic, framing, checksum code.

## Search targets (imports / strings)
`winusb.dll`, `WinUsb_Initialize`, `WinUsb_ReadPipe`, `WinUsb_WritePipe`,
`WinUsb_ControlTransfer`, `CreateFileW`, `SetupDiGetClassDevs`,
`SetupDiEnumDeviceInterfaces`, `DeviceIoControl`, `VID_0483`, `PID_5265`,
`AUTOPHIX_DM`, `Autophix`, the two interface GUIDs, and:
`firmware`, `update`, `upgrade`, `download`, `version`, `serial`, `device info`,
`checksum`, `crc`, `md5`, `sha`, `ack`, `nack`, `packet`, `command`, `bootloader`.

## Findings (to be completed)
### VERIFIED
_none yet_
### STRONG INFERENCE
_none yet_
### WEAK INFERENCE
_none yet_
### UNKNOWN
Everything about the updater's protocol construction.
