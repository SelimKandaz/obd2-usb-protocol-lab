# Protocol Status

Legend - **Status**: done / partial / blocked / not started.
**Safe to query** means an independently executable read-only request is defined
and permitted today.

| Feature | Status | Evidence | Confidence | Safe to query | Implemented |
|---|---|---|---|---|---|
| USB enumeration | done | live PnP and WinUSB enumeration | VERIFIED | yes | `client/winusb.py` |
| Endpoint discovery | done | live descriptors plus static `WinUsb_QueryPipe` | VERIFIED | yes | `vod700 endpoints` |
| Device identity | done | injected/live standard descriptor, VID/PID | VERIFIED | yes | `vod700 descriptors` |
| Updater detection handshake | partial | bounded capture completed; no updater URB appeared | VERIFIED zero-traffic result | n/a | analyzer ready |
| Heartbeat / polling | not started | none observed in 18 seconds | UNKNOWN | n/a | detector ready |
| Firmware version query | blocked | no static/dynamic request match | UNKNOWN | no | gated |
| Storage information | blocked | static `0x0B` candidate only | MEDIUM meaning | no | none |
| Bulk read behavior | blocked | static `0x06` candidate only; no dynamic transfer | MEDIUM meaning | no | reassembler ready |
| 16-byte interrupt framing | partial | updater code verifies width/endpoints; no captured frame | HIGH | n/a | `framing.py` |
| Request checksum | partial | updater builder verifies additive sum8; no captured frame | HIGH | n/a | `checksums.py` |
| Response checksum | not started | none | UNKNOWN | n/a | detector ready |
| ACK / NACK | not started | static opcode relationship only | LOW | n/a | models ready |
| Firmware container | partial | opaque high-entropy containers; no execution | MEDIUM | n/a | static report |

## Current safety gate

`identify` and `version` remain disabled, `UNSAFE`, and `UNKNOWN`. The accepted
capture contains zero packets on `0x01`, `0x81`, `0x02`, and `0x82`; vendor
commands `0x0B` and `0x06` were not observed. No active request is approved.
