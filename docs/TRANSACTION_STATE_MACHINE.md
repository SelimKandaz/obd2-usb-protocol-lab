# Evidence-backed Transaction State Machine

The first updater exchange is represented in `vod700.client.transaction` and
`vod700.protocol.verified`.

```text
policy gate
    -> write 16-byte 0x0B on interrupt OUT 0x01
    -> read exactly 16 bytes on interrupt IN 0x81 (1,000 ms timeout)
    -> validate AA55 magic, response command 0x8B, and SUM8
    -> expose little-endian value 0x02000000
```

The transport is injected. `ReplayDevice` is used for the automated path; the
shipped policy refuses before any transport call. The request remains
`ACTIVE_QUERY`, not `READ_ONLY`, because its meaning and state-change risk are
not proven harmless and the official updater proceeds into update-state logic.

The `0x06` block-read and `0x02` bulk-write paths are deliberately not exposed
as active state-machine operations. The latter is classified dangerous and has
no builder. This module does not send bytes to a physical device.

`WinUsbPipeTransport` and the low-level overlapped WinUSB pipe methods are
implemented, but policy remains the only dispatch gate. Descriptor probing does
not call them, and no live vendor request has been authorized in this project.
