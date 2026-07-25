# Handshake Analysis

Date: 2026-07-24

## Current evidence

The first updater-idle capture remains a valid negative result: `Update.exe`
launched with no arguments, stayed idle for 18 seconds, and generated no live
vendor traffic. The new reconnect capture validates USBPcap itself, but it was
performed with `Update.exe` closed.

## Capture-path validation

- USBPcap interface: `\\.\USBPcap1`
- VOD700 root-hub location: `Port_#0009.Hub_#0001`
- Initial USBPcap address: 5
- Reconnected USBPcap address: 6
- Source: `C:\USBPcapCaptures\VOD700_reconnect_20260724_202512.pcap`
- Source size: 1,134 bytes
- Source SHA-256: `344604CCD58B8BF27AC10F85980C58AF2372AF488770B27CE4C0A9DA8B17536E`
- Canonical PCAPNG: `private_samples\captures\baseline_reconnect.pcapng`
- Canonical size: 1,556 bytes
- Canonical SHA-256: `3484911891084476D74E8D3553D15F13BE5676E09EED241388E7E5AEC4182878`

## Result

The reconnect trace has 20 live control records and no interrupt or bulk
records. It proves the backend and interface mapping are genuine, but it does
not provide a vendor handshake, 16-byte command frame, checksum instance,
heartbeat, or read-only command candidate.

The earlier idle capture's vendor-command conclusion is unchanged: `0x0B` and
`0x06` did not appear, and no active request is enabled.
