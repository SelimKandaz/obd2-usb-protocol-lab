# Protocol Status

| Feature | Status | Evidence | Confidence | Safe to query |
|---|---|---|---|---|
| USB enumeration | done | 20 live endpoint-0 records; addresses 5 -> 6 | VERIFIED LIVE | yes |
| USBPcap root-hub mapping | done | genuine reconnect capture on `\\.\USBPcap1` | VERIFIED LIVE | n/a |
| Endpoint discovery | done | live descriptors declare `0x81`, `0x01`, `0x82`, `0x02` | VERIFIED LIVE | yes |
| Updater idle handshake | partial | 18-second idle capture has no live vendor URB | VERIFIED negative | n/a |
| Updater-open reconnect behavior | blocked | not captured | UNKNOWN | n/a |
| Runtime file/device observation | not started | updater was closed for reconnect baseline | UNKNOWN | n/a |
| Update-button handler map | blocked | exact MFC resource/cross-reference map incomplete | UNKNOWN | no |
| 16-byte interrupt framing | partial | static updater builder only; no live frame | HIGH static | n/a |
| Request checksum | partial | static additive sum8 only; no live frame | HIGH static | n/a |
| Heartbeat / polling | not started | no interrupt traffic | UNKNOWN | no |
| Firmware version query | blocked | no command identified | UNKNOWN | no |
| Storage query (`0x0B`) | blocked | static candidate only | MEDIUM meaning | no |
| Block read (`0x06`) | blocked | static candidate only | MEDIUM meaning | no |
| Response checksum / ACK | not started | no vendor response | UNKNOWN | no |

## Safety gate

`identify` and `version` remain disabled. No vendor request has been sent. The
genuine reconnect capture validates the transport only; it does not promote a
read-only command.
