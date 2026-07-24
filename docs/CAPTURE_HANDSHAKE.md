# Capture Workflow - Passive Handshake

The orchestrator records the updater detecting the USB-only VOD700 while idle.
It never sends a project-generated vendor request and never interacts with an
update control.

## Automated workflow

Dry run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 `
  -UpdaterPath "private_samples\updater\Update.exe" `
  -DurationSeconds 18 `
  -DryRun
```

Owner-approved elevated run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\capture_updater_handshake.ps1 `
  -UpdaterPath "private_samples\updater\Update.exe" `
  -DurationSeconds 18
```

The script:

1. verifies the VOD700 and capture tools
2. enumerates USBPcap interfaces
3. finds the unique WinUSB target in each extcap device tree
4. filters to that USBPcap address
5. creates a bounded named-pipe sink before starting USBPcap
6. launches the updater with no arguments
7. waits 18 seconds without UI interaction
8. calls `CloseMainWindow`
9. stops the pipe and USBPcap process
10. converts the private raw stream to PCAPNG, hashes it, and runs the analyzer

## Address warning

`DEVPKEY_Device_Address` can describe the physical hub port and may differ from
USBPcap's current bus address. On the 2026-07-24 run, Windows reported 9 while
USBPcap reported 4 on `\\.\USBPcap1`. Always use the extcap device-tree mapping.

## Analysis

```powershell
.\.venv\Scripts\python.exe -m vod700 capture analyze `
  private_samples\captures\<capture>.pcapng --out reports --prefix handshake

.\.venv\Scripts\python.exe -m vod700 capture checksums `
  private_samples\captures\<capture>.pcapng --endpoint 0x01
```

USBPcap descriptor injection creates synthetic capture-start records with IRP
ID zero. Correlate those setup/descriptor pairs separately from live updater
submit/completion URBs before counting endpoint traffic.
