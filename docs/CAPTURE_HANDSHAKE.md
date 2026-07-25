# Capture Workflow - Passive Handshake

The initial updater-idle trace was negative. A separate complete-root-hub
reconnect capture has now validated the USBPcap path with real traffic.

## Verified reconnect command shape

The supplied capture was made with USBPcapCMD equivalent to:

```powershell
USBPcapCMD.exe -d \\\.\USBPcap1 -A -o C:\USBPcapCaptures\VOD700_reconnect_20260724_202512.pcap
```

`-A` captured the complete selected root hub and descriptor injection was not
enabled. Zero-IRP descriptor records from `--inject-descriptors` are synthetic
and must not be counted as live traffic.

## Interpretation rules

- USBPcap `info=0` is a submit record; `info=1` is a completion record.
- Nonzero IRP IDs identify live kernel-observed records.
- Zero IRP IDs classify USBPcap injected descriptors.
- USB addresses may change across reconnects; do not hard-code address 4 or 9.
- Standard control enumeration is not a VOD700 vendor command.

The accepted baseline is `private_samples\captures\baseline_reconnect.pcapng`.
The next updater-open capture must be compared against that baseline and must
stop before any button-triggered write.
