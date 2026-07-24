# Capture Tooling Report

Date: 2026-07-24. Host username/paths redacted.

## VERIFIED LIVE

| Tool | Version/state |
|---|---|
| Wireshark / tshark / dumpcap | 4.6.7 |
| USBPcapCMD | installed |
| USBPcap kernel driver | running |
| VOD700 | present at USB address 9, `Port_#0009.Hub_#0001` |
| Verified capture control device | `\\.\USBPcap1` |

The port/address must be rechecked after reconnect. The VOD700 remains bound to
Microsoft WinUSB; no device driver was replaced.

## dumpcap integration limitation

`dumpcap -D` lists network interfaces only despite the running USBPcap driver.
Passing `\\.\USBPcap1` directly to dumpcap fails with Windows error 123. This is
a Wireshark/USBPcap enumeration integration issue, not evidence that the kernel
driver is absent.

The orchestrator now supports direct `USBPcapCMD` capture when an explicit
control device is supplied. It restricts capture to the current USB device
address and injects descriptors. Its classic pcap output is supported by the
native analyzer.

## VERIFIED DRY RUN

- backend: `USBPcapCMD`
- interface: `\\.\USBPcap1`
- device address: 9
- duration: 18 seconds
- updater arguments: none
- close: `CloseMainWindow`, force-stop only after a 3-second grace period
- destination: git-ignored `private_samples/captures/`

## BLOCKED

Direct capture requires elevated PowerShell. Two elevation launch attempts did
not receive UAC approval before the caller timed out. No updater process
appeared and no capture file was created. The next action is owner approval of
the UAC prompt for this same bounded passive capture.
