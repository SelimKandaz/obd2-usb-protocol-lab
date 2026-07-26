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

The transport is injected. `ReplayDevice` is used for the automated path. The
request/response is now verified by a physical exchange, so the policy class is
`READ_ONLY`; it remains disabled by default and is enabled only for the
explicit `vod700 storage-query --approve-live` invocation.

The `0x06` block-read and `0x02` bulk-write paths are deliberately not exposed
as active state-machine operations. The latter is classified dangerous and has
no builder. This module does not send bytes to a physical device.

`WinUsbPipeTransport` and the low-level overlapped WinUSB pipe methods are
implemented, but policy remains the only dispatch gate. Descriptor probing does
not call them. The opt-in command restores the disabled policy after one
transaction and exposes the exact request/response bytes for auditability.
