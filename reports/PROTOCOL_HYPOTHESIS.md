# Protocol Hypothesis

Date: 2026-07-24

No passive handshake capture was available at this checkpoint.

## VERIFIED STATICALLY

The updater's interrupt request builder produces 16-byte frames:

| Offset | Meaning |
|---:|---|
| 0 | `0x55` |
| 1 | `0xAA` |
| 2 | command |
| 3–14 | command-specific data/padding |
| 15 | `sum(frame[0:15]) & 0xFF` |

It writes through selector 1 (`0x01` interrupt OUT) and reads exactly 16 bytes
through selector 0 (`0x81` interrupt IN). Callers expect response command byte
`request[2] + 0x80`.

## HIGH CONFIDENCE

- Framing is fixed-width 16 bytes on the interrupt channel.
- The request checksum is additive sum8, not CRC-8.
- Address/size fields observed in commands `0x06` and `0x0B` are little-endian.
- PID `0x5265` follows the updater's DM100 branch.

## MEDIUM CONFIDENCE

- Command `0x0B` is a capacity/size query: response bytes 3–6 are interpreted as
  a little-endian size and control later address ranges.
- Command `0x06` is a block-read setup request: bytes 3–6 contain an address,
  byte 8 is `0x10`, and success is followed by bulk-IN reads.
- Response byte 2 is an ACK/response opcode.

These meanings are not safe-to-query classifications.

## LOW CONFIDENCE

- Commands `0x03` and `0x0A` are long operations, inferred only from special
  20-second and 120-second timeout branches.
- Command `0x07` participates in a non-PID-`0x5265` path; its meaning is unknown.

## UNKNOWN

- passive timeline and endpoint packet counts
- response checksum validation
- heartbeat/repeated payload
- status/NACK layout
- device-info/model/version command
- bulk fragmentation on the VOD700
- whether any statically seen command is independently safe to send

No command satisfies the two-source rule. `identify` and `version` remain
disabled and classified `UNSAFE`/`UNKNOWN`.
