# Environment Report

Current repository evidence snapshot: 2026-07-26.

## Host and toolchain

The research host is Windows 11 x64 with PowerShell 5.1 and multiple Python
versions. The project virtual environment is the reproducible execution target
for the package and test suite. Git, Python, pytest, Ruff, mypy, and wheel
build tooling are available in the repository workflow.

## USB capture tooling

- Wireshark/tshark/dumpcap 4.6.7: installed and used during capture work
- USBPcapCMD and the USBPcap kernel component: installed and used
- Verified capture control device: `\\.\USBPcap1`
- USBPcap device addresses are dynamic and must be discovered per session
- The native analyzer consumes classic PCAP/PCAPNG without requiring tshark

The original capture-installation blocker is historical. The canonical private
captures are already present and must not be repeated merely to refresh this
report.

## Device

- PnP instance: `USB\VID_0483&PID_5265\AUTOPHIX_DM`
- Service: Microsoft `WINUSB` / `winusb.inf`
- Product: `Automotive Diagnostic Device`
- Address: dynamic; canonical updater capture used bus 1/address 6

See `docs/DEVICE_PROFILE.md` and `docs/USB_ENDPOINTS.md` for the verified
descriptor facts.

## Private samples

The official updater and its private containers exist under
`private_samples/updater/`. They are ignored by Git. Firmware/update images
remain static-analysis-only and are never executed, transmitted, or committed.
