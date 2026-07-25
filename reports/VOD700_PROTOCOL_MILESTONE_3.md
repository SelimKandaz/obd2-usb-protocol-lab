# VOD700 Protocol - Milestone 3

Date: 2026-07-24

Milestone 3's updater-idle capture completed safely but contained only six
zero-IRP synthetic USBPcap descriptor records. The later reconnect capture now
validates the USBPcap path with 20 nonzero-IRP live enumeration records; see
`VOD700_PROTOCOL_MILESTONE_4.md` and `USBPCAP_RECONNECT_VALIDATION.md`.

Static updater findings remain valid: WinUSB endpoint discovery, 16-byte
interrupt framing, additive request checksum, and blocked candidates `0x0B` and
`0x06`. No vendor request was sent and no policy command was promoted.
