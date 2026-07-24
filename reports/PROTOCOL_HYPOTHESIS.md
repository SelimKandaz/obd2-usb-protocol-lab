# Protocol Hypothesis

Date: 2026-07-24

## VERIFIED

- The VOD700 descriptor declares interrupt OUT `0x01`, interrupt IN `0x81`,
  bulk OUT `0x02`, and bulk IN `0x82`.
- The accepted 18-second updater capture contains no live transfers on those
  endpoints.
- Vendor command bytes `0x0B` and `0x06` did not appear.

## HIGH - static evidence only

- Interrupt requests and responses are 16 bytes.
- Request bytes 0 and 1 are `55 AA`.
- Request byte 2 is the command.
- Request byte 15 is `sum(frame[0:15]) & 0xFF`.
- Requests use `0x01`; responses use `0x81`.

These remain high-confidence protocol hypotheses but are not dynamically
validated by this capture.

## MEDIUM - static meaning only

- `0x0B` is a capacity/size query candidate.
- `0x06` is a block-read setup candidate followed by bulk IN.

Neither meaning establishes that independent transmission is safe.

## UNKNOWN

- automatic-detection trigger
- device information/version command
- response checksum and status layout
- heartbeat cadence
- actual 16-byte request/response examples
- whether any vendor request is independently safe

No command satisfies the two-source rule.
