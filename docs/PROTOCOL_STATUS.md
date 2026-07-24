# Protocol Status

Legend — **Status**: ✅ done · 🟡 partial · ⛔ blocked · ⬜ not started.
**Confidence**: VERIFIED · HIGH · MEDIUM · LOW · UNKNOWN.
**Safe to query**: is a *read-only* query for this defined and permitted today?

| Feature                    | Status | Evidence                                   | Confidence | Safe to query | Implemented |
|----------------------------|:------:|--------------------------------------------|------------|:-------------:|-------------|
| USB enumeration            |   ✅   | live `vod700 devices` + PnP dump           | VERIFIED   | yes           | `client/winusb.py` |
| Endpoint discovery         |   ✅   | live `WinUsb_QueryPipe` + dump             | VERIFIED   | yes           | `vod700 endpoints` |
| Device identity (VID/PID/strings) | ✅ | live device-descriptor read             | VERIFIED   | yes           | `vod700 descriptors` |
| Serial number              |   ✅   | string descriptor #3 = `Autophix DM`       | VERIFIED   | yes (fixed)   | `vod700 descriptors` |
| Updater detection handshake| ⛔    | needs USB capture (USBPcap not installed)  | UNKNOWN    | n/a           | analyzer ready |
| Heartbeat / polling        | ⬜    | none yet                                    | UNKNOWN    | n/a           | detector ready (`repeated_payloads`) |
| Firmware version query     | ⬜    | none yet                                    | UNKNOWN    | no (gated)    | gated in `policy.py` |
| Language / region          | ⬜    | none yet                                    | UNKNOWN    | no            | — |
| Storage information        | ⬜    | none yet                                    | UNKNOWN    | no            | — |
| Update-mode status         | ⬜    | none yet                                    | UNKNOWN    | no            | — |
| Bulk transfer behavior     | ⬜    | endpoints known; behavior not captured     | LOW        | no            | reassembler ready (`framing`) |
| Framing (16B interrupt)    | 🟡    | endpoint size known; layout unknown        | LOW        | n/a           | `framing.py` |
| Checksum / CRC             | ⬜    | none yet                                    | UNKNOWN    | n/a           | detectors ready (`checksums.py`) |
| ACK / NACK behavior        | ⬜    | none yet                                    | UNKNOWN    | n/a           | models ready |
| Error responses            | ⬜    | none yet                                    | UNKNOWN    | n/a           | models ready |
| Firmware container format  | ⛔    | needs an updater/firmware sample           | UNKNOWN    | n/a           | analyzer TBD |

## Summary
Everything that can be learned from the device **without sending vendor traffic**
is VERIFIED: identity, strings, endpoints. Everything that requires observing the
updater↔device conversation is **blocked on evidence**, waiting on two owner
actions (see `reports/VOD700_PROTOCOL_MILESTONE_2.md`):

1. **USBPcap** — Wireshark/tshark/dumpcap 4.6.7 are now installed, but USBPcap
   (the USB capture driver) is not; installing it needs UAC + a reboot.
2. **Updater binary** — the official ANCEL VOD700 upgrade software is behind an
   account sign-in on anceltech.com, which the assistant cannot pass; the owner
   must download it into `private_samples/updater/`.

The tooling to analyze both inputs is built and tested; it is waiting for
evidence, not code.
